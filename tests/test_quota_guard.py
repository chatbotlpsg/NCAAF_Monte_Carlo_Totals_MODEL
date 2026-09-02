import pytest
from ncaaf_aita.data.odds import OddsApiAdapter, OddsQuotaBlocked, QuotaPolicy


def test_quota_fails_closed():
    x=object.__new__(OddsApiAdapter)
    x.policy=QuotaPolicy(min_remaining=100)
    x.last_remaining=101
    with pytest.raises(OddsQuotaBlocked):
        x._guard(2)
