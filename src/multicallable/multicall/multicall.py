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
from web3 import Web3
from web3.contract import Contract
from web3.exceptions import BadFunctionCallOutput

from .constants import MULTICALL_ABI, MULTICALL_ADDRESS, CHAIN_NANE, DEFAULT_MAKER_DAO_MULTICALL_ADDRESS
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
        if args is not None and not isinstance(args, list) and not isinstance(args, tuple):
            args = [args]
        call_data = contract.encodeABI(fn_name=fn_name, args=args, kwargs=kwargs)
        self.target = contract.address
        self.abi = contract.abi
        self.fn_name = fn_name
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
            custom_chain_name: str = None
    ):
        if custom_address:
            address = Web3.to_checksum_address(custom_address)
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

    def call(
            self,
            calls: List[Call],
            require_success: bool = True,
            block_identifier: Union[str, int] = 'latest',
    ) -> Tuple[int, bytes, List[Any]]:
        """
        Executes multicall for specified list of smart contracts functions.

        Parameters:
            calls: list(tuple)
                list of Call objets

            require_success: bool
                if true, all calls must return true, otherwise the multicall fails.

            block_identifier: Union[str, int]
                block identifier for web3 call

        Returns:
            block number of fetched data
            block hash of fetched data
            list of outputs (fetched data)
        """
        if block_identifier != 'latest':
            kwargs = dict(block_identifier=block_identifier)
        else:
            kwargs = dict()
        block_number, block_hash, return_data = self.contract.functions.tryBlockAndAggregate(
            require_success, [(call.target, call.call_data) for call in calls]).call(**kwargs)

        outputs = []
        for call, (success, data) in zip(calls, return_data):
            if not success:
                try:
                    error_message = ''.join(chr(c) for c in data if chr(c).isprintable())
                except:
                    error_message = 'Error'
                outputs.append(ValueError(error_message))
                continue
            for item in call.abi:
                if item.get('name') == call.fn_name:
                    out_types = tuple(get_type(schema) for schema in item['outputs'])
                    if out_types and not data:
                        if require_success:
                            raise BadFunctionCallOutput("Could not call contract function for a Call. "
                                                        "Check Call's contract address correctness.")
                        else:
                            outputs.append(BadFunctionCallOutput())
                            break
                    decoded_output = decode(out_types, data)
                    if len(item['outputs']) == 1:
                        decoded_output = decoded_output[0]
                    outputs.append(decoded_output)
                    break

        return block_number, block_hash, outputs
