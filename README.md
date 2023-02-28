## Multicallable

Easy way to work with Multicall package

### Installation

```shell
pip install -U multicallable
```

### Usage

Importing Web3
```python
>>> from web3 import Web3
```

Initializing Web3 instance
```python
>>> ETH_RPC_URL = 'https://rpc.ankr.com/eth'
>>> w3 = Web3(Web3.HTTPProvider(ETH_RPC_URL))
```

Importing Multicallable
```python
>>> from multicallable import Multicallable
```

Initializing Multicallable instance for Deus token
```python
# ERC20 ABI string is cropped for readability
>>> ERC20_ABI = '[{"constant":true,"inputs":[],"name":"name", ...
>>> DEUS_TOKEN = '0xDE5ed76E7c05eC5e4572CfC88d1ACEA165109E44'
>>> deus = Multicallable(DEUS_TOKEN, ERC20_ABI, w3)
```

Calling balanceOf function for a list of addresses
```python
>>> addresses = [
...     '0xa345c89c07fEB0A13937eecE0204327271904cB7',
...     '0xF493284a730e3D561Bf81f52991AF0C8D9227C35',
...     '0x19dceFD603ea112CF547Cdddb8D68f61c6F4c73C',
...     '0x633cBf6347ddddb5fEc65ad803b4e0B282ADdBd7',
... ]
>>> deus.balanceOf(addresses).call()
[3955776201653330000000,
 1499972538000000000000,
 334010000000000000000,
 135760891050327000000]
```

#### Get more details for call
```python
>>> addresses = [
...     '0xa345c89c07fEB0A13937eecE0204327271904cB7',
...     '0xF493284a730e3D561Bf81f52991AF0C8D9227C35',
...     '0x19dceFD603ea112CF547Cdddb8D68f61c6F4c73C',
...     '0x633cBf6347ddddb5fEc65ad803b4e0B282ADdBd7',
... ]
>>> deus.balanceOf(addresses).detailed_call()
[{'block_number': 54040756,
  'result': [3955776201653330000000,
             1499972538000000000000,
             334010000000000000000,
             135760891050327000000]}]
```

#### Ignore failed calls

If `require_success` is `True`, all calls must return true, otherwise the multicall fails. \
The default value is `True`.
```python
>>> contract_address = '0x15BB7787Be4E03E6Caa09D2fF502564D3eD67Ec2'
>>> contract_abi = '[{"inputs":[{"internalType":"uint256","name":"num","type":"uint256"}],"name":"getNum","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"pure","type":"function"}]'
>>> mc = Multicallable(contract_address, contract_abi, w3)
>>> mc.getNum(list(range(7))).call(require_success=True)
Traceback (most recent call last):
.
.
.
web3.exceptions.ContractLogicError: execution reverted: Multicall3: call failed

>>> mc.getNum(list(range(7))).call(require_success=False)
[ValueError('Bad number!'),
 2,
 3,
 4,
 5,
 ValueError('Bad number!'),
 7]
```

#### Change number of buckets

Set `n` as the number of buckets for calling Multicall contract for large number of calls. \
The default value is `1`.
```python
>>> result = mc.getNum(list(range(70000))).call(require_success=False)
Traceback (most recent call last):
.
.
.
ValueError: {'code': -32000, 'message': 'out of gas'}

>>> result = mc.getNum(list(range(70000))).call(require_success=False, n=100)
>>> len(result)
70000
```

#### Show progress bar
Use `progress_bar=True` to show progress bar while sending buckets.
```python
>>> result = mc.getNum(list(range(70000))).call(n=100, progress_bar=True, require_success=False)
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100/100 buckets
>>> len(result)
70000
```

#### Use with custom Multicall

It is possible to pass a Multicall instance with custom address and abi to Multicallable
```python
>>> from multicallable.multicall import Multicall
>>> multicall = Multicall(w3, custom_address, custom_abi)
>>> mc = Multicallable(contract_address, contract_abi, multicall=multicall)
```
