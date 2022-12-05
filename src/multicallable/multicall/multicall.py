"""NAME
    Multicall

DESCRIPTION
    A multicall for use with pure Web3 library.
    It uses MakerDao Multicall smart contract by default,
    but also can use any custom multicall smart contract
    that implements "tryBlockAndAggregate" function

"""

from typing import List

from eth_abi import decode_single
from web3 import Web3
from web3.contract import Contract

from .constants import MULTICALL_ABI, MULTICALL_ADDRESS, CHAIN_NANE


def get_type(schema):
    if schema.get('internalType', '').startswith('struct'):
        return '(' + ','.join(get_type(x) for x in schema['components']) + ')'
    return schema.get('internalType', schema['type'])


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

    """

    def __init__(
            self,
            contract: Contract,
            fn_name: str,
            args: list
    ):
        if not isinstance(args, list) and not isinstance(args, tuple):
            args = [args]
        call_data = contract.encodeABI(fn_name=fn_name, args=args)
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

    """

    def __init__(
            self,
            w3: Web3,
            custom_address: str = None,
            custom_abi: str = None
    ):
        if custom_address:
            address = Web3.toChecksumAddress(custom_address)
        else:
            chain_id = w3.eth.chain_id
            try:
                address = Web3.toChecksumAddress(MULTICALL_ADDRESS[CHAIN_NANE[chain_id]])
            except KeyError:
                raise ValueError(f'Chain ID {chain_id} is not in default dictionary')

        abi = custom_abi or MULTICALL_ABI

        self.contract = w3.eth.contract(address=address, abi=abi)

    def call(
            self,
            calls: List[Call],
            require_success: bool = True,
    ) -> list:
        """
        Executes multicall for specified list of smart contracts functions.

        Parameters:
            calls: list(tuple)
                list of Call objets

            require_success: bool
                if true, all calls must return true, otherwise the multicall fails.

        Returns:
            list of outputs
        """

        block_number, block_hash, return_data = self.contract.functions.tryBlockAndAggregate(
            require_success, [(call.target, call.call_data) for call in calls]).call()

        outputs = []
        for call, result in zip(calls, return_data):
            success, data = result
            for item in call.abi:
                if item.get('name') == call.fn_name:
                    out_type = '(' + ','.join(get_type(schema) for schema in item['outputs']) + ')'
                    decoded_output = decode_single(out_type, data)
                    outputs.append(decoded_output)
                    break

        return outputs
