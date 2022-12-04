from web3 import Web3

from .multicall import Multicall, Call


def split(a, n):
    k, m = divmod(len(a), n)
    return (a[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(n))


class Multicallable:
    class Function:
        def __init__(self, name: str, parent: 'Multicallable'):
            self.name = name
            self.parent = parent

        def __call__(self, params: list, n: int = 1) -> list:
            mc = self.parent.multicall
            calls = [Call(self.parent.target, self.name, args) for args in params]
            result = []
            for bucket in split(calls, n):
                if not bucket:
                    continue
                result.extend(mc.call(bucket))
            return result

    def __init__(self, w3: Web3, target_address: str, target_abi: str):
        self.multicall = Multicall(w3)
        self.target = w3.eth.contract(w3.toChecksumAddress(target_address), abi=target_abi)
        self._setup_functions()

    def _setup_functions(self):
        for func in filter(lambda x: x.get('stateMutability') in ('view', 'pure'), self.target.abi):
            self.__setattr__(func['name'], Multicallable.Function(func['name'], self))
