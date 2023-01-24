from web3 import Web3

from .multicall import Multicall, Call


def _split(a, n):
    k, m = divmod(len(a), n)
    return (a[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(n))


class Multicallable:
    class Function:
        class FCall:
            def __init__(self, function: 'Multicallable.Function', params: list):
                self.function = function
                self.params = params

            def call(self, n: int = 1, require_success: bool = True):
                mc = self.function.parent._multicall
                calls = [Call(self.function.parent._target, self.function.name, args) for args in self.params]
                result = []
                for bucket in _split(calls, n):
                    if not bucket:
                        continue
                    block_number, block_hash, outputs = mc.call(bucket, require_success=require_success)
                    result.extend(outputs)
                return result

            def detailed_call(self, n: int = 1, require_success: bool = True):
                mc = self.function.parent._multicall
                calls = [Call(self.function.parent._target, self.function.name, args) for args in self.params]
                result = []
                for bucket in _split(calls, n):
                    if not bucket:
                        continue
                    block_number, block_hash, outputs = mc.call(bucket, require_success=require_success)
                    if not result or result[-1]['block_number'] != block_number:
                        result.append(dict(block_number=block_number, result=[]))
                    result[-1]['result'].extend(outputs)
                return result

        def __init__(self, name: str, parent: 'Multicallable'):
            self.name = name
            self.parent = parent

        def __call__(self, params: list) -> list:
            return self.FCall(self, params)

    def __init__(self, target_address: str, target_abi: str, w3: Web3 = None, multicall: Multicall = None):
        if not w3 and not multicall:
            raise TypeError("__init__() missing 1 required argument: 'w3' or 'multicall' (at least one required)")
        self._multicall = multicall or Multicall(w3)
        w3 = self._multicall.contract.web3
        self._target = w3.eth.contract(w3.toChecksumAddress(target_address), abi=target_abi)
        self._functions = {}
        self._setup_functions()

    def __getattr__(self, function_name: str) -> 'Multicallable.Function':
        if function_name not in self._functions:
            raise AttributeError(f"The function '{function_name}' was not found in this contract's abi.")
        return self._functions[function_name]

    def _setup_functions(self):
        for func in filter(lambda x: x.get('stateMutability') in ('view', 'pure'), self._target.abi):
            function = Multicallable.Function(func['name'], self)
            self._functions[func['name']] = function
            setattr(self, func['name'], function)
