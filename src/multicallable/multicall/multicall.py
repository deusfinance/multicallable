"""NAME
    Multicall

DESCRIPTION
    A multicall for use with pure Web3 library.
    It uses MakerDao Multicall smart contract by default,
    but also can use any custom multicall smart contract
    that implements "tryBlockAndAggregate" function

"""

from typing import List, Union, Tuple, Any, Optional

from eth_abi import decode
from eth_typing import HexStr
from eth_utils import get_normalized_abi_inputs, get_aligned_abi_inputs
from web3 import Web3
from web3.contract.contract import Contract, ContractFunction
from web3.exceptions import BadFunctionCallOutput
from web3.types import BlockIdentifier, StateOverride, TxParams
from web3.utils import get_abi_element
from web3._utils.contracts import encode_abi  # noqa

from .constants import MULTICALL_ABI, MULTICALL_ADDRESS, CHAIN_NANE, DEFAULT_MAKER_DAO_MULTICALL_ADDRESS, \
    MULTICALL_BYTECODE
from ..utils import get_type


class Call:
    """
    NAME
        Multicall

    ATTRIBUTES
        contract: Web3.eth.Contract
            A Web3.eth.Contract instance of a contract
            that is to be called via multicall.

        fn_name: str
            The name of a contract function to be called.

        args: list
            A list of arguments to be passed to a called contract function.

        kwargs: dict
            keyword arguments to be passed to a called contract function.

    """

    def __init__(
            self,
            contract: Contract,
            fn_name: str,
            args: Optional[Union[list, tuple]] = None,
            kwargs: Optional[dict] = None,
    ):
        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}
        if args and not isinstance(args, (list, tuple)):
            args = [args]
        call_data = contract.encode_abi(abi_element_identifier=fn_name, args=args, kwargs=kwargs)
        self.target = contract.address
        self.abi = get_abi_element(contract.abi, fn_name, *args, abi_codec=contract.w3.codec, **kwargs)
        self.call_data = call_data


class Multicall:
    """
    NAME
        Multicall

    DESCRIPTION
       The main multicall class.

    ATTRIBUTES
        w3: Web3 class instance

        custom_address: str
            An address of custom multicall smart contract.
            If specified, MakerDao Multicall smart contract will be omitted.

        custom_abi: str
            An ABI of custom multicall smart contract.
            If omitted, MakerDao Multicall smart contract ABI will be used.

        custom_chain_name: str
            A custom name for provider chain.
            Use for loading MakerDao Multicall smart contract address from default dictionary.

    """

    def __init__(
            self,
            w3: Web3,
            custom_address: str = None,
            custom_abi: str = None,
            custom_chain_name: str = None,
            impersonated_address: str = None
    ):
        self._impersonated = False
        if custom_address:
            address = Web3.to_checksum_address(custom_address)
        elif impersonated_address:
            self._impersonated = True
            address = Web3.to_checksum_address(impersonated_address)
        else:
            address = DEFAULT_MAKER_DAO_MULTICALL_ADDRESS
            if custom_chain_name:
                try:
                    address = Web3.to_checksum_address(MULTICALL_ADDRESS[custom_chain_name.lower()])
                except KeyError:
                    pass
                    # raise ValueError(f'Chain name `{custom_chain_name}` is not in default dictionary')
            else:
                chain_id = w3.eth.chain_id
                try:
                    address = Web3.to_checksum_address(MULTICALL_ADDRESS[CHAIN_NANE[chain_id]])
                except KeyError:
                    pass
                    # raise ValueError(f'Chain ID {chain_id} is not in default dictionary')

        abi = custom_abi or MULTICALL_ABI

        self.contract = w3.eth.contract(address=address, abi=abi)

    def _encode_data(self, function: ContractFunction) -> HexStr:
        fn_inputs = get_normalized_abi_inputs(function.abi, *function.args, **function.kwargs)
        _, aligned_fn_inputs = get_aligned_abi_inputs(function.abi, fn_inputs)
        return encode_abi(self.contract.w3, function.abi, aligned_fn_inputs, function.selector)

    def call(
            self,
            calls: List[Union[Call, ContractFunction]],
            require_success: bool = True,
            block_identifier: BlockIdentifier = None,
            transaction: Optional[TxParams] = None,
            state_override: Optional[StateOverride] = None,
            ccip_read_enabled: Optional[bool] = None
    ) -> Tuple[int, bytes, List[Any]]:
        """
        Executes multicall for specified list of smart contracts functions.

        Parameters:
            calls: list(tuple)
                list of Call or ContractFunction objects

            require_success: bool
                if true, all calls must return true, otherwise the multicall fails.

            block_identifier: BlockIdentifier
                block identifier for web3 call

            transaction: TxParams
                dictionary of transaction info for web3 call

            state_override: StateOverride
                state override for web3 call

            ccip_read_enabled: bool
                boolean flag that enables or disables CCIP Read support for web3 calls

        Returns:
            block number of fetched data
            block hash of fetched data
            list of outputs (fetched data)
        """
        if self._impersonated:
            if state_override is None:
                state_override = {self.contract.address: dict(code=MULTICALL_BYTECODE)}
            elif self.contract.address in state_override:
                state_override[self.contract.address]['code'] = MULTICALL_BYTECODE
            else:
                state_override[self.contract.address] = dict(code=MULTICALL_BYTECODE)

        input_data = [(call.target, call.call_data) if isinstance(call, Call) else
                      (call.address, self._encode_data(call)) for call in calls]
        block_number, block_hash, return_data = self.contract.functions.tryBlockAndAggregate(
            require_success, input_data).call(
            transaction=transaction,
            block_identifier=block_identifier,
            state_override=state_override,
            ccip_read_enabled=ccip_read_enabled
        )

        outputs = []
        for call, (success, data) in zip(calls, return_data):
            if not success:
                try:
                    error_message = ''.join(chr(c) for c in data if chr(c).isprintable())
                except:
                    error_message = 'Error'
                outputs.append(ValueError(error_message))
                continue

            out_types = tuple(get_type(schema) for schema in call.abi['outputs'])
            if out_types and not data:
                if require_success:
                    raise BadFunctionCallOutput("Could not call contract function for a Call. "
                                                "Check Call's contract address correctness.")
                else:
                    outputs.append(BadFunctionCallOutput())
                    continue
            decoded_output = decode(out_types, data)
            if len(call.abi['outputs']) == 1:
                decoded_output = decoded_output[0]
            outputs.append(decoded_output)

        return block_number, block_hash, outputs
