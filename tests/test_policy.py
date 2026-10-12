from revolutx_bot.policy import Policy


def test_kill_switch():
    p = Policy(kill_switch=True)
    assert p.check_proposal(
        pair="BTC-EUR", side="buy", notional=10, risk=1, capital=100, rr=2.0
    )


def test_allowlist():
    p = Policy(asset_allowlist=("BTC-EUR",))
    assert p.check_pair("ETH-EUR") is not None
    assert p.check_pair("BTC-EUR") is None


def test_max_notional():
    p = Policy(max_trade_notional=50)
    assert p.check_proposal(
        pair="BTC-EUR", side="buy", notional=100, risk=1, capital=1000, rr=2.0
    )


def test_ok_proposal():
    p = Policy()
    assert (
        p.check_proposal(
            pair="BTC-EUR", side="buy", notional=50, risk=1, capital=1000, rr=2.0
        )
        is None
    )
