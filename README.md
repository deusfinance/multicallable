## Multicallable

Easy way to work with Multicall package

### Installation

```shell
pip install multicallable
```

### Usage

```python
>>> from multicallable import Multicallable
>>> multicallable_usdc = Multicallable(w3, USDC_ADDRESS, ERC20_ABI)
>>> multicallable_usdc.balanceOf([[w3.toChecksumAddress(user)] for user in users])
[(4735413200308,), (4729400125935,), (4721283019561,), (4768773839572,)]
```