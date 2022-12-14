from web3 import Web3

from .multicall import Multicall, Call


def _split(a, n):
    k, m = divmod(len(a), n)
    return (a[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(n))


class Multicallable:
    class Function:
        def __init__(self, name: str, parent: 'Multicallable'):
            self.name = name
            self.parent = parent

        def __call__(self, params: list, n: int = 1, require_success: bool = True) -> list:
            mc = self.parent.multicall
            calls = [Call(self.parent.target, self.name, args) for args in params]
            result = []
            for bucket in _split(calls, n):
                if not bucket:
                    continue
                result.extend(mc.call(bucket, require_success=require_success))
            return result

    def __init__(self, target_address: str, target_abi: str, w3: Web3 = None, multicall: Multicall = None):
        if not w3 and not multicall:
            raise TypeError("__init__() missing 1 required argument: 'w3' or 'multicall' (at least one required)")
        self.multicall = multicall or Multicall(w3)
        w3 = self.multicall.contract.web3
        self.target = w3.eth.contract(w3.toChecksumAddress(target_address), abi=target_abi)
        self._setup_functions()

    def _setup_functions(self):
        for func in filter(lambda x: x.get('stateMutability') in ('view', 'pure'), self.target.abi):
            self.__setattr__(func['name'], Multicallable.Function(func['name'], self))
