"""NAME
    Multicall

DESCRIPTION
    A multicall for use with pure Web3 library.
    It uses MakerDao Multicall smart contract by default,
    but also can use any custom multicall smart contract
    that implements "tryBlockAndAggregate" function

"""

from typing import List, Union, Optional

from eth_abi import decode_single
from eth_account.signers.local import LocalAccount
from eth_typing import BlockNumber, ChecksumAddress, HexStr
from hexbytes import HexBytes
from web3 import Web3
from web3.contract import Contract
from web3.types import Wei, LogReceipt

from .constants import MULTICALL_ABI, MULTICALL_ADDRESS, CHAIN_NANE


def get_type(schema):
    if schema.get('internalType', '').startswith('struct'):
        postfix = '[]' if schema['internalType'].endswith('[]') else ''
        return '(' + ','.join(get_type(x) for x in schema['components']) + ')' + postfix
    elif schema.get('internalType', '').startswith('enum'):
        return schema['type']
    return schema.get('internalType', schema['type'])


class TxReceipt:
    def __init__(self, receipt: dict):
        self.block_hash: HexBytes = receipt.get('blockHash')
        self.block_number: BlockNumber = receipt.get('blockNumber')
        self.contract_address: Optional[ChecksumAddress] = receipt.get('contractAddress')
        self.cumulative_gas_used: int = receipt.get('cumulativeGasUsed')
        self.effective_gas_price: int = receipt.get('effectiveGasPrice')
        self.gas_used: Wei = receipt.get('gasUsed')
        self.from_: ChecksumAddress = receipt.get('from')
        self.logs: List[LogReceipt] = receipt.get('logs')
        self.logs_bloom: HexBytes = receipt.get('logsBloom')
        self.root: HexStr = receipt.get('root')
        self.status: int = receipt.get('status')
        self.to: ChecksumAddress = receipt.get('to')
        self.transaction_hash: HexBytes = receipt.get('transactionHash')
        self.transaction_index: int = receipt.get('transactionIndex')

    def successful(self) -> bool:
        return bool(self.status)


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
            args: Union[list, tuple] = None,
            kwargs: dict = None,
    ):
        if not isinstance(args, list) and not isinstance(args, tuple):
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
        self.w3 = w3
        if custom_address:
            address = Web3.toChecksumAddress(custom_address)
        else:
            if custom_chain_name:
                try:
                    address = Web3.toChecksumAddress(MULTICALL_ADDRESS[custom_chain_name.lower()])
                except KeyError:
                    raise ValueError(f'Chain name `{custom_chain_name}` is not in default dictionary')
            else:
                chain_id = w3.eth.chain_id
                try:
                    address = Web3.toChecksumAddress(MULTICALL_ADDRESS[CHAIN_NANE[chain_id]])
                except KeyError:
                    raise ValueError(f'Chain ID {chain_id} is not in default dictionary')

        abi = custom_abi or MULTICALL_ABI

        self.contract = w3.eth.contract(address=address, abi=abi)

    def execute(
            self,
            calls: List[Call],
            transaction_params: dict,
            account: LocalAccount,
            require_success: bool = True,
    ) -> TxReceipt:
        raw_transaction = self.contract.functions.tryAggregate(
            require_success, [(call.target, call.call_data) for call in calls])
        for param in ('from', 'nonce', 'gasPrice'):
            if param not in transaction_params:
                raise ValueError(f'Missing param: {param}')

        transaction = raw_transaction.buildTransaction(transaction_params)
        if require_success:
            estimated_gas = self.w3.eth.estimate_gas(transaction)
            if 'gas' not in transaction_params:
                gas_limit = round(estimated_gas * 1.5)
                transaction['gas'] = gas_limit

        signed_transaction = account.sign_transaction(transaction)
        self.w3.eth.send_raw_transaction(signed_transaction.rawTransaction)
        transaction_hash = self.w3.toHex(signed_transaction.hash)
        print(transaction_hash)
        receipt = self.w3.eth.wait_for_transaction_receipt(transaction_hash)
        return TxReceipt(receipt)

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
            if not success or not data:
                try:
                    error_message = ''.join(chr(c) for c in data[-32:] if c)
                except:
                    error_message = 'Error'
                outputs.append(ValueError(error_message))
                continue
            for item in call.abi:
                if item.get('name') == call.fn_name:
                    out_type = '(' + ','.join(get_type(schema) for schema in item['outputs']) + ')'
                    decoded_output = decode_single(out_type, data)
                    if len(item['outputs']) == 1:
                        decoded_output = decoded_output[0]
                    outputs.append(decoded_output)
                    break

        return block_number, block_hash, outputs
