#!/usr/bin/env python3
"""An experimental dashboard for daily reports on portfolio composition and changes.
"""
import argparse
import functools

from beancount.core.amount import to_decimal, Decimal
from beancount import loader
from beancount.ops import prices
from beancount.ops import holdings
from beancount.reports import rholdings
from beancount.parser import options


def join(holdings_list, features_map, keyfun):
    """Join a list of holdings with a vector of arbitrary features.

    This function joins a list of holdings with a features_map, where the join
    key between the two mappings is provided by a configuration callable
    'keyfun'. keyfun() is run on every holding, and the resulting key is looked
    up from features_map.

    All the values from features_map are first normalized to 100%, and when
    aggregating, the 'market_value' attribute of the holdings is multiplied by
    the normalized feature value.

    Args:
      holdings_list: A list of holdings.Holding instances.
      features_map: A dict of some key to a dict of features. The values are
        dicts of strings to a number.
      keyfun: A function that produces the join key from a Holding instance.
        The key is used to look up a feature vector from the features_map dict.
    Returns:
      A dict of labels (from the values of features_map) to a Decimal number
      of market_value amounts.
    """
    # Get the full list of features.
    all_labels = set(label
                     for features in features_map.values()
                     for label in features)
    features_total = {label: to_decimal('0')
                      for label in all_labels}

    # Normalize the feature vectors.
    norm_features_map = {key: normalize_features(features)
                         for key, features in features_map.items()}

    # Accumulate the market value of each holding in buckets for each label.
    for holding in holdings_list:
        key = keyfun(holding)
        try:
            features = norm_features_map[key]
            for label, fraction in features.items():
                if not holding.market_value:
                    continue
                features_total[label] += (
                    holding.market_value * to_decimal(fraction))
        except KeyError:
            raise KeyError("Key {} not found in mapping: {}".format(
                repr(key), norm_features_map))

    return features_total


def normalize_features(features_dict):
    """Normalize the values of a dictionary to sum to 1.0.

    Args:
      features_dict: A dict of any type of key to a number.
    Returns:
      A new dict, whose values have been scaled so that they
      all sum to 1.0.
    """
    total_values = sum(features_dict.values())
    return {label: value/total_values
            for label, value in features_dict.items()}


def getitem_startswith(adict, key):
    """A dict getter which returns the first key of dict matching the start of 'key'.

    Args:
      adict: a dict object.
      key: A string, the value to match against the dict keys.
    Returns:
      A key and value from 'adict'.
    """
    assert isinstance(key, str)
    for dict_key, dict_value in adict.items():
        if dict_key and key.startswith(dict_key):
            return dict_key, dict_value
    return None, None


def startswith_key_getter(features_map, holding):
    """Return first key from features_map that matches the holding's account name.

    Args:
      features_map: A dict of key to features (also dicts).
      holding: An instance of Holding.
    Returns:
      One of the keys of features_map.
    """
    key, _ = getitem_startswith(features_map, holding.account)
    return key


def print_features(title, features, currency):
    """Print a features aggregation.

    Args:
      title: A string, the title to printfor this section.
      features: A dict of label strings to numbers.
      currency: A string, the currency to output.
    """
    if not features:
        return

    print(title)
    label_width = max(24, max(len(label) for label in features))
    total_value = sum(features.values())
    for label, value in sorted(features.items(), key=lambda x: x[1], reverse=1):
        frac = value / total_value
        print('  {:{width}}  {:>16.2f} {} ( {:>6.1%} )'.format(
            label, value, currency, frac,
            width=label_width))
    print()


def dashboard_main():
    parser = argparse.ArgumentParser(__doc__.strip())
    parser.add_argument('holdings_filename', help='Holdings CSV filename')
    parser.add_argument('prices_filename', help='Prices Beancount filename')
    parser.add_argument('currency', help="Currency to convert all market values to.")
    opts = parser.parse_args()

    # Load the price database.
    # Generate with "bean-query LEDGER holdings"
    price_entries, _, options_map = loader.load(opts.prices_filename, quiet=True)
    price_map = prices.build_price_map(price_entries)

    # Load the holdings list.
    # Generate with "bean-query LEDGER print_prices"
    mixed_holdings_list = list(rholdings.load_from_csv(open(opts.holdings_filename)))

    # Convert all the amounts to a common currency (otherwise summing market
    # values makes no sense).
    holdings_list = holdings.convert_to_currency(price_map, opts.currency,
                                                 mixed_holdings_list)

    # Create a mapping of cost currencies. This can be derived automatically, no
    # need to create this one manually.
    currency_features = {
        holding.currency: {holding.cost_currency: 1}
        for holding in mixed_holdings_list}

    return holdings_list, opts.currency, currency_features


if __name__ == '__main__':
    main()