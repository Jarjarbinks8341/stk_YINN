from production_strategy import YINNProductionStrategy
from backtest import load_data

def get_latest_signal():
    data = load_data()
    strategy = YINNProductionStrategy(lookback=60)
    result = strategy.get_current_signal(data)
    return result

def calculate_put_strategy(capital=15000):
    # Get current market data from our production system
    result = get_latest_signal()
    
    current_price = result['current_price']
    support = result['support']
    
    # Selection Logic
    # 1. Conservative strike: Nearest whole number below support
    conservative_strike = int(support)
    # 2. Moderate strike: Nearest whole number near support
    moderate_strike = round(support)
    
    print("=" * 60)
    print(f"YINN CASH SECURED PUT STRATEGY (Capital: ${capital:,.2f})")
    print("=" * 60)
    print(f"Current Price: ${current_price:.2f}")
    print(f"60-Day Support: ${support:.2f}")
    print("-" * 60)
    
    for name, strike in [("CONSERVATIVE", conservative_strike), ("MODERATE", moderate_strike)]:
        collateral_per_contract = strike * 100
        num_contracts = int(capital // collateral_per_contract)
        total_collateral = num_contracts * collateral_per_contract
        reserve = capital - total_collateral
        
        distance_to_strike = ((current_price - strike) / current_price) * 100
        
        print(f"[{name} STRIKE: ${strike:.2f}]")
        print(f"  Contracts:      {num_contracts}")
        print(f"  Collateral:     ${total_collateral:,.2f}")
        print(f"  Cash Reserve:   ${reserve:,.2f}")
        print(f"  Margin of Safety: {distance_to_strike:.1f}% below current price")
        print("-" * 30)

    print("\nRECOMMENDATION:")
    print(f"1. Sell {int(capital // (conservative_strike * 100))} contracts of the ${conservative_strike} Put.")
    print(f"2. Aim for 30-45 days until expiration.")
    print(f"3. If assigned, your cost basis will be ${conservative_strike} (minus premium).")
    print("=" * 60)

if __name__ == "__main__":
    calculate_put_strategy(15000)
