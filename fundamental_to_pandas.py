import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import time
import warnings

warnings.filterwarnings('ignore')


class FundamentalDataScraper:
    """
    A comprehensive fundamental data scraper for stock analysis
    """

    def __init__(self, tickers, add_index=True):
        """
        Initialize the scraper with tickers

        Parameters:
        -----------
        tickers : list
            List of stock tickers
        add_index : bool
            Whether to add .JK suffix for Indonesian stocks
        """
        self.tickers = []
        for ticker in tickers:
            if add_index and not ticker.endswith('.JK'):
                self.tickers.append(f"{ticker}.JK")
            else:
                self.tickers.append(ticker)

        self.results = []
        self.errors = []

    def get_industry_classification(self, ticker):
        """
        Get detailed industry classification for a ticker
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            # Get industry and sector information
            industry = info.get('industry', 'Unknown')
            sector = info.get('sector', 'Unknown')

            # Additional business summary for classification
            summary = info.get('longBusinessSummary', '')

            # Classify into more specific categories
            detailed_industry = self.classify_industry(industry, sector, summary, ticker)

            return {
                'industry': industry,
                'sector': sector,
                'detailed_industry': detailed_industry,
                'summary': summary[:200] if summary else ''
            }
        except:
            return {
                'industry': 'Unknown',
                'sector': 'Unknown',
                'detailed_industry': 'Unclassified',
                'summary': ''
            }

    def classify_industry(self, industry, sector, summary, ticker):
        """
        Classify stocks into detailed industry categories
        """
        ticker_upper = ticker.upper()

        # Banking classification
        banking_keywords = ['bank', 'banque', 'bancorp', 'bancshares']
        if any(keyword in industry.lower() for keyword in banking_keywords) or \
                any(keyword in summary.lower() for keyword in banking_keywords):
            return 'Banking'

        # Insurance classification
        insurance_keywords = ['insurance', 'assurance', 'underwriting', 'reinsurance']
        if any(keyword in industry.lower() for keyword in insurance_keywords) or \
                any(keyword in summary.lower() for keyword in insurance_keywords):
            return 'Insurance'

        # Financing/Lending classification
        finance_keywords = ['financ', 'lending', 'credit', 'loan', 'leasing', 'mortgage',
                            'consumer finance', 'capital markets', 'investment', 'broker',
                            'asset management', 'securities', 'exchange']
        if any(keyword in industry.lower() for keyword in finance_keywords) or \
                any(keyword in summary.lower() for keyword in finance_keywords) or \
                sector.lower() == 'financial services':
            # Sub-classify financial services
            if 'consumer' in summary.lower() or 'multi' in industry.lower():
                return 'Consumer Finance'
            elif 'investment' in industry.lower() or 'broker' in industry.lower():
                return 'Investment Services'
            elif 'capital' in industry.lower() or 'securities' in industry.lower():
                return 'Capital Markets'
            else:
                return 'Financial Services'

        # Technology classification
        tech_keywords = ['software', 'technology', 'tech', 'digital', 'internet', 'app', 'platform']
        if any(keyword in industry.lower() for keyword in tech_keywords) or \
                sector.lower() == 'technology':
            return 'Technology'

        # Healthcare classification
        healthcare_keywords = ['health', 'hospital', 'medical', 'pharma', 'drug', 'biotech', 'clinic']
        if any(keyword in industry.lower() for keyword in healthcare_keywords) or \
                any(keyword in summary.lower() for keyword in healthcare_keywords) or \
                sector.lower() == 'healthcare':
            return 'Healthcare'

        # Consumer Goods classification
        consumer_keywords = ['consumer', 'retail', 'food', 'beverage', 'tobacco', 'household',
                             'personal', 'apparel', 'textile', 'restaurant']
        if any(keyword in industry.lower() for keyword in consumer_keywords) or \
                any(keyword in summary.lower() for keyword in consumer_keywords):
            return 'Consumer Goods & Retail'

        # Energy & Mining classification
        energy_keywords = ['oil', 'gas', 'energy', 'mining', 'coal', 'petroleum', 'drilling']
        if any(keyword in industry.lower() for keyword in energy_keywords) or \
                any(keyword in summary.lower() for keyword in energy_keywords) or \
                sector.lower() == 'energy':
            return 'Energy & Mining'

        # Property & Real Estate classification
        property_keywords = ['real estate', 'property', 'development', 'construction', 'building']
        if any(keyword in industry.lower() for keyword in property_keywords) or \
                any(keyword in summary.lower() for keyword in property_keywords):
            return 'Property & Real Estate'

        # Infrastructure & Utilities
        infra_keywords = ['utility', 'infrastructure', 'telecom', 'toll', 'airport', 'port']
        if any(keyword in industry.lower() for keyword in infra_keywords) or \
                any(keyword in summary.lower() for keyword in infra_keywords) or \
                sector.lower() == 'utilities':
            return 'Infrastructure & Utilities'

        # Manufacturing
        manufacturing_keywords = ['manufactur', 'industrial', 'chemical', 'cement', 'steel',
                                  'metal', 'machinery', 'automotive', 'auto parts']
        if any(keyword in industry.lower() for keyword in manufacturing_keywords) or \
                any(keyword in summary.lower() for keyword in manufacturing_keywords) or \
                sector.lower() == 'industrials':
            return 'Manufacturing'

        # Agriculture
        agriculture_keywords = ['agriculture', 'plantation', 'palm oil', 'farming', 'fishery']
        if any(keyword in industry.lower() for keyword in agriculture_keywords) or \
                any(keyword in summary.lower() for keyword in agriculture_keywords):
            return 'Agriculture'

        # Transportation
        transport_keywords = ['transport', 'logistic', 'shipping', 'airline', 'railway', 'courier']
        if any(keyword in industry.lower() for keyword in transport_keywords) or \
                any(keyword in summary.lower() for keyword in transport_keywords):
            return 'Transportation & Logistics'

        return 'Other'

    def get_financial_ratios(self, ticker):
        """
        Extract comprehensive financial ratios
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            # Get financial statements
            try:
                balance_sheet = stock.balance_sheet
                if balance_sheet.empty:
                    balance_sheet = stock.quarterly_balance_sheet
            except:
                balance_sheet = pd.DataFrame()

            try:
                income_stmt = stock.financials
                if income_stmt.empty:
                    income_stmt = stock.quarterly_financials
            except:
                income_stmt = pd.DataFrame()

            try:
                cash_flow = stock.cashflow
                if cash_flow.empty:
                    cash_flow = stock.quarterly_cashflow
            except:
                cash_flow = pd.DataFrame()

            # Extract fundamental data
            fundamentals = {
                # Company Info
                'Company_Name': info.get('longName', info.get('shortName', ticker)),
                'Ticker': ticker,
                'Current_Price': info.get('currentPrice', info.get('regularMarketPrice', None)),
                'Market_Cap': info.get('marketCap', None),
                'Enterprise_Value': info.get('enterpriseValue', None),

                # Valuation Ratios
                'PER': info.get('trailingPE', info.get('forwardPE', None)),
                'Forward_PER': info.get('forwardPE', None),
                'PEG_Ratio': info.get('pegRatio', None),
                'PBV': info.get('priceToBook', None),
                'PS_Ratio': info.get('priceToSalesTrailing12Months', None),
                'PC_Ratio': None,  # Will calculate if possible
                'EV_EBITDA': info.get('enterpriseToEbitda', None),
                'EV_Revenue': info.get('enterpriseToRevenue', None),

                # Profitability Ratios
                'Gross_Margin': None,
                'Operating_Margin': None,
                'Net_Profit_Margin': None,
                'ROA': None,
                'ROE': None,
                'ROIC': None,

                # Growth Metrics
                'Revenue_Growth_YoY': info.get('revenueGrowth', None),
                'Earnings_Growth_YoY': info.get('earningsGrowth', None),

                # Financial Health
                'Current_Ratio': info.get('currentRatio', None),
                'Quick_Ratio': info.get('quickRatio', None),
                'Debt_to_Equity': info.get('debtToEquity', None),
                'Debt_to_Assets': None,
                'Interest_Coverage': None,

                # Dividend Metrics
                'Dividend_Yield': info.get('dividendYield', None),
                'Dividend_Rate': info.get('dividendRate', None),
                'Payout_Ratio': info.get('payoutRatio', None),

                # Stock Metrics
                'Beta': info.get('beta', None),
                '52_Week_High': info.get('fiftyTwoWeekHigh', None),
                '52_Week_Low': info.get('fiftyTwoWeekLow', None),
                'Avg_Volume': info.get('averageVolume', None),
                'Shares_Outstanding': info.get('sharesOutstanding', None),
                'Float_Shares': info.get('floatShares', None),

                # Per Share Data
                'EPS_TTM': info.get('trailingEps', None),
                'Book_Value_Per_Share': info.get('bookValue', None),
                'Revenue_Per_Share': info.get('revenuePerShare', None),
                'Free_Cash_Flow_Per_Share': None,

                # Additional Metrics
                'EBITDA': info.get('ebitda', None),
                'Total_Revenue': info.get('totalRevenue', None),
                'Net_Income': info.get('netIncomeToCommon', None),
                'Total_Debt': info.get('totalDebt', None),
                'Total_Cash': info.get('totalCash', None),
                'Free_Cash_Flow': info.get('freeCashflow', None),
                'Operating_Cash_Flow': info.get('operatingCashflow', None)
            }

            # Calculate derived ratios from financial statements
            if not income_stmt.empty and not balance_sheet.empty:
                try:
                    # Get latest period values
                    latest_bs = balance_sheet.iloc[:, 0]
                    latest_is = income_stmt.iloc[:, 0]

                    # Revenue and profit
                    total_revenue = latest_is.get('Total Revenue', None)
                    gross_profit = latest_is.get('Gross Profit', None)
                    operating_income = latest_is.get('Operating Income', None)
                    net_income = latest_is.get('Net Income', None)

                    # Balance sheet items
                    total_assets = latest_bs.get('Total Assets', None)
                    total_equity = latest_bs.get('Total Stockholder Equity', None)
                    total_debt = latest_bs.get('Total Debt', latest_bs.get('Long Term Debt', None))
                    current_assets = latest_bs.get('Current Assets', None)
                    current_liabilities = latest_bs.get('Current Liabilities', None)
                    inventory = latest_bs.get('Inventory', None)

                    # Calculate margins
                    if total_revenue and total_revenue != 0:
                        if gross_profit:
                            fundamentals['Gross_Margin'] = gross_profit / total_revenue
                        if operating_income:
                            fundamentals['Operating_Margin'] = operating_income / total_revenue
                        if net_income:
                            fundamentals['Net_Profit_Margin'] = net_income / total_revenue

                    # Calculate ROA and ROE
                    if net_income and total_assets and total_assets != 0:
                        fundamentals['ROA'] = net_income / total_assets
                    if net_income and total_equity and total_equity != 0:
                        fundamentals['ROE'] = net_income / total_equity

                    # Calculate ROIC
                    if operating_income and total_assets and current_liabilities:
                        invested_capital = total_assets - current_liabilities
                        if invested_capital != 0:
                            fundamentals['ROIC'] = (operating_income * 0.8) / invested_capital

                    # Calculate Debt to Assets
                    if total_debt and total_assets and total_assets != 0:
                        fundamentals['Debt_to_Assets'] = total_debt / total_assets

                    # Calculate Interest Coverage
                    interest_expense = latest_is.get('Interest Expense', None)
                    if operating_income and interest_expense and interest_expense != 0:
                        fundamentals['Interest_Coverage'] = operating_income / abs(interest_expense)

                    # Calculate Free Cash Flow per Share
                    if fundamentals['Free_Cash_Flow'] and fundamentals['Shares_Outstanding']:
                        fundamentals['Free_Cash_Flow_Per_Share'] = \
                            fundamentals['Free_Cash_Flow'] / fundamentals['Shares_Outstanding']

                except Exception as e:
                    pass

            # Convert ratios to percentages where appropriate
            for ratio in ['Gross_Margin', 'Operating_Margin', 'Net_Profit_Margin',
                          'ROA', 'ROE', 'ROIC', 'Debt_to_Assets']:
                if fundamentals[ratio] is not None:
                    fundamentals[ratio] = fundamentals[ratio] * 100

            # Convert dividend yield to percentage
            if fundamentals['Dividend_Yield'] is not None:
                fundamentals['Dividend_Yield'] = fundamentals['Dividend_Yield'] * 100

            # Round all numeric values
            for key in fundamentals.keys():
                if isinstance(fundamentals[key], (int, float)):
                    fundamentals[key] = round(fundamentals[key], 4)

            return fundamentals

        except Exception as e:
            self.errors.append({'ticker': ticker, 'error': str(e)})
            return None

    def scrape_additional_data(self, ticker):
        """
        Scrape additional data from web sources (optional)
        """
        # This can be extended to scrape from other sources
        additional_data = {
            'analyst_target': None,
            'analyst_recommendation': None,
            'short_interest': None,
            'institutional_ownership': None
        }

        try:
            # Example: Get analyst recommendations from Yahoo Finance
            stock = yf.Ticker(ticker)
            info = stock.info

            additional_data['analyst_target'] = info.get('targetMeanPrice', None)
            additional_data['analyst_recommendation'] = info.get('recommendationKey', None)
            additional_data['short_interest'] = info.get('shortPercentOfFloat', None)
            additional_data['institutional_ownership'] = info.get('heldPercentInstitutions', None)

        except:
            pass

        return additional_data

    def run_analysis(self, delay=0.5):
        """
        Run comprehensive fundamental analysis for all tickers

        Parameters:
        -----------
        delay : float
            Delay between API calls in seconds to avoid rate limiting
        """
        print(f"Starting fundamental analysis for {len(self.tickers)} tickers...")
        print(f"Estimated time: {len(self.tickers) * delay / 60:.1f} minutes")
        print("-" * 80)

        for i, ticker in enumerate(self.tickers):
            print(f"Processing {i + 1}/{len(self.tickers)}: {ticker}")

            # Get industry classification
            industry_data = self.get_industry_classification(ticker)

            # Get financial ratios
            financial_data = self.get_financial_ratios(ticker)

            # Get additional data
            additional_data = self.scrape_additional_data(ticker)

            if financial_data:
                # Combine all data
                combined_data = {
                    **financial_data,
                    'Sector': industry_data['sector'],
                    'Industry': industry_data['industry'],
                    'Detailed_Industry': industry_data['detailed_industry'],
                    **additional_data
                }
                self.results.append(combined_data)
                print(f"  ✓ Success - {industry_data['detailed_industry']}")
            else:
                self.errors.append({'ticker': ticker, 'error': 'Failed to fetch financial data'})
                print(f"  ✗ Failed")

            # Add delay to avoid rate limiting
            if i < len(self.tickers) - 1:
                time.sleep(delay)

        print("-" * 80)
        print(f"Analysis complete!")
        print(f"Successful: {len(self.results)} | Failed: {len(self.errors)}")

        return self.create_dataframe()

    def create_dataframe(self):
        """
        Create a pandas DataFrame from the results
        """
        if not self.results:
            print("No results to create DataFrame")
            return pd.DataFrame()

        df = pd.DataFrame(self.results)

        # Set Ticker as index (optional)
        # df.set_index('Ticker', inplace=True)

        # Sort by industry and company name
        df = df.sort_values(['Detailed_Industry', 'Company_Name'])

        return df

    def save_to_csv(self, filename=None):
        """
        Save results to CSV file
        """
        if not self.results:
            print("No results to save")
            return

        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'fundamental_analysis_{timestamp}.csv'

        df = self.create_dataframe()
        df.to_csv(filename, index=False)
        print(f"Results saved to {filename}")

        return filename

    def get_industry_summary(self):
        """
        Get summary statistics by industry
        """
        if not self.results:
            return pd.DataFrame()

        df = self.create_dataframe()

        # Group by detailed industry and calculate averages
        industry_stats = df.groupby('Detailed_Industry').agg({
            'Ticker': 'count',
            'Current_Price': 'mean',
            'Market_Cap': 'median',
            'PER': 'median',
            'PBV': 'median',
            'ROE': 'median',
            'Net_Profit_Margin': 'median',
            'Debt_to_Equity': 'median',
            'Dividend_Yield': 'mean'
        }).round(2)

        industry_stats.rename(columns={'Ticker': 'Count'}, inplace=True)
        industry_stats = industry_stats.sort_values('Count', ascending=False)

        return industry_stats


# Example usage
if __name__ == "__main__":
    # Define your tickers
    tickers = [
        'AALI', 'ARTO', 'ASGR', 'ASII', 'AUTO',
        'BBCA', 'BBNI', 'BBRI', 'BBTN', 'BDMN',
        'BJBR', 'BJTM', 'BMRI', 'BNGA', 'BNLI',
        'BRIS', 'BTPS', 'BTPN', 'HEAL', 'ICBP',
        'INDF', 'KLBF', 'MARK', 'MIKA', 'NISP',
        'OMED', 'PNBN', 'POWR', 'SIDO', 'SMSM',
        'TLKM', 'TSPC', 'UNTR', 'MLBI', 'DLTA',
        'GOTO', 'BUKA', 'EMTK', 'ISAT', 'EXCL',  # Added some tech/telco
        'ADRO', 'PTBA', 'ITMG', 'UNVR', 'HMSP',  # Added mining/consumer
    ]

    # Initialize scraper
    scraper = FundamentalDataScraper(tickers, add_index=True)

    # Run analysis
    df = scraper.run_analysis(delay=0.3)  # 0.3 second delay between requests

    # Display results
    if not df.empty:
        print("\n" + "=" * 80)
        print("FUNDAMENTAL ANALYSIS RESULTS")
        print("=" * 80)

        # Display first few rows
        print("\nSample of results:")
        print(df[['Ticker', 'Company_Name', 'Detailed_Industry', 'PER', 'PBV', 'ROE', 'Net_Profit_Margin']].head(10))

        # Industry summary
        print("\nIndustry Distribution:")
        industry_dist = df['Detailed_Industry'].value_counts()
        print(industry_dist)

        # Industry statistics
        print("\nIndustry Averages:")
        industry_stats = scraper.get_industry_summary()
        print(industry_stats)

        # Save to CSV
        scraper.save_to_csv()

        # Additional analysis examples
        print("\n" + "=" * 80)
        print("ADDITIONAL ANALYSIS EXAMPLES")
        print("=" * 80)

        # Banking sector analysis
        banking_stocks = df[df['Detailed_Industry'] == 'Banking']
        if not banking_stocks.empty:
            print("\nBanking Sector Analysis:")
            print(banking_stocks[['Ticker', 'PER', 'PBV', 'ROE', 'Net_Profit_Margin', 'Debt_to_Equity']])

        # Cheap stocks (Low PER)
        cheap_stocks = df[df['PER'].notna() & (df['PER'] > 0) & (df['PER'] < 15)]
        if not cheap_stocks.empty:
            print("\nPotentially Undervalued (PER < 15):")
            print(cheap_stocks[['Ticker', 'Company_Name', 'PER', 'PBV', 'ROE']].sort_values('PER'))

        # High ROE stocks
        high_roe = df[df['ROE'].notna() & (df['ROE'] > 15)]
        if not high_roe.empty:
            print("\nHigh ROE Stocks (>15%):")
            print(high_roe[['Ticker', 'Company_Name', 'ROE', 'PER', 'PBV']].sort_values('ROE', ascending=False))