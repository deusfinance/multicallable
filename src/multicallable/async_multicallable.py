import asyncio
from typing import Union, Tuple

from web3 import AsyncWeb3

from .multicall.async_multicall import AsyncCall, AsyncMulticall
from .utils import split, bar


class AsyncMulticallable:
    class Function:
        class FCall:
            def __init__(self, function: 'AsyncMulticallable.Function', params: list):
                self.function = function
                self.params = params

            async def call(self, n: int = 1, require_success: bool = True, progress_bar: bool = False,
                           block_identifier: Union[str, int] = 'latest'):
                mc = self.function.parent._multicall
                calls = [AsyncCall(self.function.parent._target, self.function.name, args) for args in self.params]
                result = []
                prepared_calls = []

                for i, bucket in enumerate(split(calls, n)):
                    if not bucket:
                        continue
                    task = mc.call(bucket, require_success=require_success, block_identifier=block_identifier,
                                   metadata=i)
                    prepared_calls.append(task)

                if progress_bar:
                    print(f'\r    {bar(0)} {0}/{n} buckets    ', end='')

                i = 0
                batch_results = [None] * len(prepared_calls)
                for task in asyncio.as_completed(prepared_calls):
                    task_result = await task
                    if progress_bar:
                        percentage = i / n * 100
                        print(f'\r    {bar(percentage)} {i}/{n} buckets    ', end='')
                        i += 1
                    block_number, block_hash, outputs, metadata = task_result
                    batch_results[metadata] = outputs

                for br in batch_results:
                    result.extend(br)

                if progress_bar:
                    print(f'\r    {bar(100)} {n}/{n} buckets    ')

                return result

            async def detailed_call(self, n: int = 1, require_success: bool = True, progress_bar: bool = False,
                                    block_identifier: Union[str, int] = 'latest'):
                mc = self.function.parent._multicall
                calls = [AsyncCall(self.function.parent._target, self.function.name, args) for args in self.params]
                result = []

                prepared_calls = []
                for i, bucket in enumerate(split(calls, n)):
                    if not bucket:
                        continue
                    prepared_calls.append(
                        mc.call(bucket, require_success=require_success, block_identifier=block_identifier, metadata=i))

                if progress_bar:
                    print(f'\r    {bar(0)} {0}/{n} buckets    ', end='')

                i = 0
                batch_results = [None] * n
                for task in asyncio.as_completed(prepared_calls):
                    task_result = await task
                    if progress_bar:
                        percentage = i / n * 100
                        print(f'\r    {bar(percentage)} {i}/{n} buckets    ', end='')
                        i += 1
                    block_number, block_hash, outputs, metadata = task_result
                    batch_results[metadata] = (outputs, block_number)

                for br in batch_results:
                    br: Tuple
                    block = br[1]
                    if not result or result[-1]['block_number'] != block:
                        result.append(dict(block_number=block, result=[]))
                    result[-1]['result'].extend(br[0])

                if progress_bar:
                    print(f'\r    {bar(100)} {n}/{n} buckets    ')

                return result

        def __init__(self, name: str, parent: 'AsyncMulticallable'):
            self.name = name
            self.parent = parent

        def __call__(self, params: list) -> FCall:
            return self.FCall(self, params)

    def __init__(self):
        self._multicall = None
        self._target = None
        self._functions = None

    async def setup(self, target_address: str, target_abi: str, w3: AsyncWeb3 = None, multicall: AsyncMulticall = None):
        if not w3 and not multicall:
            raise TypeError("__init__() missing 1 required argument: 'w3' or 'multicall' (at least one required)")
        if multicall:
            self._multicall = multicall
        else:
            self._multicall = AsyncMulticall()
            await self._multicall.setup(w3)
        w3 = self._multicall.contract.w3
        self._target = w3.eth.contract(w3.to_checksum_address(target_address), abi=target_abi)
        self._functions = {}
        self._setup_functions()

    def __getattr__(self, function_name: str) -> 'AsyncMulticallable.Function':
        if function_name not in self._functions:
            raise AttributeError(f"The function '{function_name}' was not found in this contract's abi.")
        return self._functions[function_name]

    def _setup_functions(self):
        for func in filter(lambda x: x.get('stateMutability') in ('view', 'pure'), self._target.abi):
            function = AsyncMulticallable.Function(func['name'], self)
            self._functions[func['name']] = function
            setattr(self, func['name'], function)
