# Alfred Currency Converter

*Under Construction*

## Installation

*Under Construction*

## User Guide

### Config

| Name         | Function                                                     | Default                        |
| ------------ | ------------------------------------------------------------ | ------------------------------ |
| `app_id`     | Credentials to aquire currencies rates, can be obtain at [Open Exchange Rates](https://openexchangerates.org/) |                                |
| `precision`  | Round off position after decimal point                       | `2`                            |
| `expire`     | Threshold to trigger rates update in seconds                 | `300`                          |
| `base`       | Your primary, daily-use currency                             | `USD`                          |
| `currencies` | Favorite Conversion List                                     | `["EUR", "CNY", "JPY", "GBP"]` |

### Methods

* [value]
* [currency]
* [value] [currency]
* [currency] [currency]
* [value] [currency] [currency]

## Credit

* This project is inspired by [FlyRabbit / alfred3-workflow-CurrencyX](https://github.com/FlyRabbit/alfred3-workflow-CurrencyX)

  I made this spin-off because the original one doesn't work in the way I thought it should be. As I'm trying to tweaking the the old ones, things get more out of control which ended up I've decided to re-write my own version.

* Core Library depends on the work-of-art-library: [deanishe / alfred-workflow](https://github.com/deanishe/alfred-workflow)

* API provided by [Open Exchange Rates](https://openexchangerates.org/)

* Icons made by [Freepik](https://www.freepik.com) from [Flaticon](https://www.flaticon.com) at [here](https://www.flaticon.com/free-icon/exchange_1924021) and [here](https://www.flaticon.com/packs/countrys-flags)

## License

MIT