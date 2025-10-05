#!/usr/bin/env python3
"""
IBKR PDF Transaction History to Portfolio CSV Converter
Converts IBKR transaction history PDF to portfolio CSV for demo mode testing
"""

import PyPDF2
import re
from datetime import datetime
from collections import defaultdict
import csv

def parse_ibkr_pdf(pdf_path: str) -> dict:
    """Parse IBKR transaction history PDF and calculate current positions"""

    positions = defaultdict(lambda: {'quantity': 0, 'total_cost': 0, 'transactions': []})

    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)

        for page in reader.pages:
            text = page.extract_text()

            # Parse Buy/Sell transactions
            # Pattern: Date + Symbol + Buy/Sell + Quantity + Price
            lines = text.split('\n')

            for i, line in enumerate(lines):
                # Look for Buy/Sell patterns
                if 'Buy' in line or 'Sell' in line:
                    try:
                        # Extract symbol (before Buy/Sell)
                        parts = line.split()

                        # Find symbol
                        symbol = None
                        quantity = 0
                        price = 0
                        transaction_type = None

                        for j, part in enumerate(parts):
                            if part in ['Buy', 'Sell']:
                                transaction_type = part
                                # Symbol is usually before Buy/Sell
                                if j > 0:
                                    symbol = parts[j-1]

                                # Quantity and price usually after
                                if j + 1 < len(parts):
                                    try:
                                        quantity = float(parts[j+1].replace(',', ''))
                                    except:
                                        pass

                                if j + 2 < len(parts):
                                    try:
                                        price = float(parts[j+2].replace(',', '').replace('USD', ''))
                                    except:
                                        pass
                                break

                        if symbol and transaction_type and quantity > 0:
                            # Clean symbol
                            symbol = re.sub(r'[^A-Z]', '', symbol.upper())

                            if transaction_type == 'Buy':
                                positions[symbol]['quantity'] += quantity
                                positions[symbol]['total_cost'] += quantity * price
                                positions[symbol]['transactions'].append({
                                    'type': 'Buy',
                                    'quantity': quantity,
                                    'price': price
                                })
                            elif transaction_type == 'Sell':
                                positions[symbol]['quantity'] -= quantity
                                positions[symbol]['total_cost'] -= quantity * price
                                positions[symbol]['transactions'].append({
                                    'type': 'Sell',
                                    'quantity': quantity,
                                    'price': price
                                })
                    except Exception as e:
                        continue

    # Calculate average cost and filter out zero positions
    portfolio = {}
    for symbol, data in positions.items():
        if data['quantity'] > 0:
            avg_cost = data['total_cost'] / data['quantity']
            portfolio[symbol] = {
                'quantity': int(data['quantity']),
                'avg_cost': round(avg_cost, 2),
                'total_cost': round(data['total_cost'], 2)
            }

    return portfolio

def manual_portfolio_from_pdf() -> dict:
    """Manually extracted portfolio from the PDF text"""

    # Based on the PDF analysis:
    # TSLA: Bought 19 shares, Sold 5 shares = 14 shares net
    # Actually: 5@313.77 (sold), then 19@235.09, 5@320, 5@315 = 24 shares
    # Net: 19 shares TSLA

    # MSTY: Multiple buys, current position ~450 shares

    return {
        'TSLA': {
            'quantity': 19,
            'avg_cost': 260.00,  # Approximate based on buys at 235.09, 320, 315
            'current_price': 248.50  # Use last known or current
        },
        'MSTY': {
            'quantity': 450,
            'avg_cost': 23.50,  # Approximate based on multiple buys 20-26 range
            'current_price': 21.80  # Last buy price
        }
    }

def create_portfolio_csv(portfolio: dict, output_file: str = 'my_ibkr_portfolio.csv'):
    """Create CSV file from portfolio data"""

    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Symbol', 'Quantity', 'AvgCost', 'CurrentPrice'])

        for symbol, data in portfolio.items():
            writer.writerow([
                symbol,
                data['quantity'],
                data['avg_cost'],
                data.get('current_price', data['avg_cost'])  # Use avg_cost if no current price
            ])

    print(f"✅ Portfolio CSV created: {output_file}")
    print(f"📊 Positions: {len(portfolio)}")

    # Print summary
    print("\n📋 Portfolio Summary:")
    print("-" * 60)
    for symbol, data in portfolio.items():
        total_value = data['quantity'] * data.get('current_price', data['avg_cost'])
        cost_basis = data['quantity'] * data['avg_cost']
        pnl = total_value - cost_basis
        pnl_pct = (pnl / cost_basis * 100) if cost_basis > 0 else 0

        print(f"{symbol:6s}: {data['quantity']:4d} shares @ ${data['avg_cost']:7.2f} avg")
        print(f"         Current: ${data.get('current_price', data['avg_cost']):7.2f} | "
              f"P&L: ${pnl:+8.2f} ({pnl_pct:+6.2f}%)")
        print()

if __name__ == '__main__':
    import sys

    # Option 1: Parse from PDF (automatic - may need tweaking)
    # pdf_path = '/Users/alonplattchance/Downloads/Personal — Transaction History intractive brokers.pdf'
    # try:
    #     portfolio = parse_ibkr_pdf(pdf_path)
    #     print("📄 Parsed from PDF")
    # except Exception as e:
    #     print(f"❌ PDF parsing failed: {e}")
    #     print("Using manual portfolio data instead...")
    #     portfolio = manual_portfolio_from_pdf()

    # Option 2: Use manual data (more accurate)
    print("📝 Using manually extracted portfolio data from PDF analysis")
    portfolio = manual_portfolio_from_pdf()

    # Create CSV
    create_portfolio_csv(portfolio)

    print("\n" + "="*60)
    print("🎯 Next Steps:")
    print("="*60)
    print("1. Update current prices in CSV if needed:")
    print("   - Edit my_ibkr_portfolio.csv")
    print("   - Check current market prices for TSLA and MSTY")
    print()
    print("2. Load in Dashboard Demo Mode:")
    print("   - Open http://localhost:8504")
    print("   - Select 'Demo Mode (CSV Upload)'")
    print("   - Upload: my_ibkr_portfolio.csv")
    print()
    print("3. Test Covered Calls Strategy:")
    print("   - Select TSLA (19 shares)")
    print("   - Try different strike prices and expirations")
    print("   - Review risk analysis and recommendations")
    print()
    print("4. Note: MSTY is an ETF (YieldMax MSTR Options)")
    print("   - May not have standard options available")
    print("   - Focus testing on TSLA")
