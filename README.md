## Multicallable: Simplified Interface for Multicall

`Multicallable` provides a streamlined way to work with the Multicall package, allowing you to batch multiple contract calls into a single request.

### Installation

Install the package using the following command:

```shell
pip install -U multicallable
```

### Getting Started

#### Initialize Web3 or AsyncWeb3

First, import the Web3 library and set up a Web3 instance. The setup differs depending on whether you are using synchronous or asynchronous operations.

For synchronous operations:

```python
from web3 import Web3

# Specify Ethereum RPC URL
ETH_RPC_URL = 'https://rpc.ankr.com/eth'

# Initialize Web3 instance
w3 = Web3(Web3.HTTPProvider(ETH_RPC_URL))
```

For asynchronous operations:

```python
from web3 import AsyncWeb3

# Initialize AsyncWeb3 instance
w3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(ETH_RPC_URL))
```

#### Import and Initialize Multicallable

Next, import the `Multicallable` class and initialize it for a specific token:

```python
from multicallable import Multicallable

# Truncated ERC20 ABI for demonstration
ERC20_ABI = '[{"constant":true,"inputs":[],"name":"name", ...'

# sample token contract address
TOKEN = '0xDE5ed76E7c05eC5e4572CfC88d1ACEA165109E44'

# Initialize Multicallable instance
multicallable = Multicallable(TOKEN, ERC20_ABI, w3)
```

#### AsyncMulticallable: The Asynchronous Alternative

For asynchronous use-cases, `AsyncMulticallable` is available. Unlike `Multicallable`, its constructor is empty, and it includes an asynchronous `setup` function that takes the same parameters:

```python
from multicallable import AsyncMulticallable

# Initialize AsyncMulticallable instance
async_multicallable = AsyncMulticallable()
await async_multicallable.setup(TOKEN, ERC20_ABI, w3)  # Make sure w3 is an AsyncWeb3 instance
```

### Basic Operations

#### Querying Multiple Balances

For synchronous operations:

```python
addresses = [
    # List of addresses
]
balances = multicallable.balanceOf(addresses).call()
```

For asynchronous operations:

```python
addresses = [
    # List of addresses
]
balances = await async_multicallable.balanceOf(addresses).call()
```

#### Detailed Call Information

For synchronous operations:

```python
detailed_info = multicallable.balanceOf(addresses).detailed_call()
```

For asynchronous operations:

```python
detailed_info = await async_multicallable.balanceOf(addresses).detailed_call()
```

### Advanced Features

#### Handling Failed Calls

By default, all calls must succeed for the batch call to return successfully. Use `require_success=False` to allow partial success:

```python
mc = Multicallable(contract_address, contract_abi, w3)
partial_result = mc.getNum(list(range(7))).call(require_success=False)
```

#### Batching Large Number of Calls

For large number of calls, you can specify the number of buckets using the `n` parameter:

```python
result = mc.getNum(list(range(70000))).call(require_success=False, n=100)
```

#### Progress Indicator

Enable a progress bar for better visibility into the batch processing:

```python
result = mc.getNum(list(range(70000))).call(n=100, progress_bar=True, require_success=False)
```

#### Custom Multicall Instance

You can also use a custom Multicall instance with a custom address and ABI:

```python
from multicallable.multicall import Multicall

multicall = Multicall(w3, custom_address, custom_abi)
mc = Multicallable(contract_address, contract_abi, multicall=multicall)
```

## Authors

- **[MiKO](https://github.com/MiKoronjoo)** - *Initial work*
- **[Naveed](https://github.com/naveedinno)** - *Contributor*
