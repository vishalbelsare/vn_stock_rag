# tools/financial_tools.py

from crewai.tools import BaseTool
from vnstock import Vnstock, Listing, Quote, Screener, Trading
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import json

class TechDataTool(BaseTool):
    name: str = "Công cụ tra cứu dữ liệu Phân tích Kỹ thuật"
    description: str = "Rất hữu ích để lấy dữ liệu lịch sử giá và các chỉ báo kỹ thuật cho một mã cổ phiếu hoặc chỉ số. Đầu vào là một chuỗi mã duy nhất (ví dụ: 'FPT' hoặc 'VNINDEX')."
    
    def _run(self, ticker: str) -> str:
        try:
            try:
                data = json.loads(ticker)
                if isinstance(data, dict) and 'ticker' in data: ticker = data['ticker']
            except (json.JSONDecodeError, TypeError):
                pass

            print(f"[Tech Tool] Bắt đầu lấy dữ liệu kỹ thuật cho '{ticker}'...")
            
            is_index = ticker.upper() in ["VNINDEX", "HNXINDEX", "VN30", "HNX30"]
            data_source = 'VCI' if is_index else 'TCBS'
            
            # Khởi tạo đối tượng stock một lần
            stock = Vnstock().stock(symbol=ticker, source=data_source)
            
            header = f"### Phân tích Kỹ thuật cho {ticker}\n"
            if not is_index:
                try:
                    profile_df = stock.company.profile()
                    overview_df = stock.company.overview()
                    
                    if not profile_df.empty:
                        company_name = profile_df.get('companyName', pd.Series([""])).iloc[0]
                        if company_name:
                            header = f"### Phân tích Kỹ thuật cho {ticker} ({company_name})\n"
                    
                    if not overview_df.empty:
                        industry = overview_df.get('industry', pd.Series([""])).iloc[0]
                        if industry:
                            header += f"**Ngành:** {industry}\n"
                except Exception as e:
                    print(f"[Tech Tool] Không thể lấy profile/overview cho {ticker}: {e}")

            end_date = datetime.now()
            start_date_str = (end_date - timedelta(days=365)).strftime('%Y-%m-%d')
            end_date_str = end_date.strftime('%Y-%m-%d')
            
            price_data = stock.quote.history(start=start_date_str, end=end_date_str, interval='1D')
            
            if price_data.empty: return f"Không tìm thấy dữ liệu lịch sử cho mã '{ticker}'"
            
            tech_data = self._calculate_indicators(price_data)
            support_resistance = self._find_support_resistance(price_data)
            current_price = price_data['close'].iloc[-1]
            latest_indicators = tech_data.iloc[-1]
            
            result = header
            result += f"**Ngày phân tích:** {datetime.now().strftime('%Y-%m-%d')}\n"
            result += f"**Giá đóng cửa gần nhất:** {current_price:,.2f}\n"
            result += self._get_technical_analysis(latest_indicators, current_price)
            result += f"\n**Vùng hỗ trợ/kháng cự:**\n{support_resistance}"
            
            print(f"[Tech Tool] Phân tích kỹ thuật cho '{ticker}' hoàn tất.")
            return result
            
        except Exception as e:
            print(f"Lỗi nghiêm trọng trong TechDataTool cho '{ticker}': {e}")
            import traceback
            traceback.print_exc()
            return f"Đã xảy ra lỗi nghiêm trọng khi lấy dữ liệu kỹ thuật cho mã '{ticker}'."

    # Các hàm helper không đổi
    def _calculate_indicators(self, df):
        data = df.copy().reset_index()
        data['SMA_50'] = data['close'].rolling(window=50).mean()
        data['SMA_200'] = data['close'].rolling(window=200).mean()
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / (loss.replace(0, 1e-10)) # Tránh chia cho 0
        data['RSI_14'] = 100 - (100 / (1 + rs))
        data['RSI_14'] = data['RSI_14'].fillna(50)
        data['EMA_12'] = data['close'].ewm(span=12, adjust=False).mean()
        data['EMA_26'] = data['close'].ewm(span=26, adjust=False).mean()
        data['MACD'] = data['EMA_12'] - data['EMA_26']
        data['MACD_Signal'] = data['MACD'].ewm(span=9, adjust=False).mean()
        return data

    def _find_support_resistance(self, df, window=10, threshold=0.03):
        data = df.copy()
        data['local_max'] = data['high'].rolling(window=window, center=True).apply(lambda x: x.iloc[len(x)//2] == max(x), raw=False)
        data['local_min'] = data['low'].rolling(window=window, center=True).apply(lambda x: x.iloc[len(x)//2] == min(x), raw=False)
        resistance_levels = data[data['local_max'] == 1]['high'].values
        support_levels = data[data['local_min'] == 1]['low'].values
        current_price = data['close'].iloc[-1]
        
        def cluster_levels(levels, threshold_pct):
            if len(levels) == 0: return []
            levels = sorted(levels)
            clusters = [[levels[0]]]
            for level in levels[1:]:
                if abs((level - clusters[-1][-1]) / clusters[-1][-1]) < threshold_pct:
                    clusters[-1].append(level)
                else: clusters.append([level])
            return [np.mean(cluster) for cluster in clusters]
        
        resistance_levels = sorted([r for r in cluster_levels(resistance_levels, threshold) if r > current_price])[:3]
        support_levels = sorted([s for s in cluster_levels(support_levels, threshold) if s < current_price], reverse=True)[:3]
        
        result = "".join([f"- R{i+1}: {level:,.0f} VND\n" for i, level in enumerate(resistance_levels)])
        result += "\n" + "".join([f"- S{i+1}: {level:,.0f} VND\n" for i, level in enumerate(support_levels)])
        return result
    
    def _get_technical_analysis(self, indicators, current_price):
        analysis = []
        if current_price > indicators.get('SMA_200', float('inf')): analysis.append("- Xu hướng dài hạn: TĂNG.")
        else: analysis.append("- Xu hướng dài hạn: GIẢM.")
        if current_price > indicators.get('SMA_50', float('inf')): analysis.append("- Xu hướng trung hạn: TĂNG.")
        else: analysis.append("- Xu hướng trung hạn: GIẢM.")
        rsi = indicators.get('RSI_14', 50)
        if rsi > 70: analysis.append(f"- RSI ({rsi:.2f}): Vùng QUÁ MUA, có thể điều chỉnh.")
        elif rsi < 30: analysis.append(f"- RSI ({rsi:.2f}): Vùng QUÁ BÁN, có thể hồi phục.")
        else: analysis.append(f"- RSI ({rsi:.2f}): TRUNG TÍNH.")
        macd = indicators.get('MACD', 0)
        signal = indicators.get('MACD_Signal', 0)
        if macd > signal: analysis.append("- MACD: Tín hiệu TÍCH CỰC.")
        else: analysis.append("- MACD: Tín hiệu TIÊU CỰC.")
        return "\n".join(analysis)

class ComprehensiveFinancialTool(BaseTool):
    name: str = "Công cụ Phân tích Tài chính và Cạnh tranh Toàn diện"
    description: str = "Một công cụ mạnh mẽ để phân tích tài chính nội tại và so sánh cạnh tranh. Đầu vào là một chuỗi mã cổ phiếu duy nhất (ví dụ: 'HPG')."

    def _get_industry_peers(self, ticker: str, num_peers: int = 5) -> list[str]:
        """
        Hàm tìm đối thủ, kết hợp linh hoạt giữa Screener và Listing.
        """
        print(f"[Financial Tool] Đang tìm các công ty cùng ngành với {ticker}...")
        try:
            screener = Screener()
            all_market_data_df = screener.stock(params={"exchangeName": "HOSE,HNX,UPCOM"}, limit=5000)
            if not all_market_data_df.empty:
                target_company_info = all_market_data_df[all_market_data_df['ticker'] == ticker]
                
                if not target_company_info.empty and 'industry' in target_company_info.columns:
                    industry_name = target_company_info['industry'].iloc[0]
                    print(f"[Financial Tool] Ngành của {ticker} (từ Screener) là: '{industry_name}'")

                    peers_df = all_market_data_df[all_market_data_df['industry'] == industry_name]
                    
                    if not peers_df.empty and 'market_cap' in peers_df.columns:
                        peers_sorted_df = peers_df.sort_values(by='market_cap', ascending=False)
                        peers_list = peers_sorted_df['ticker'].tolist()
                        if ticker in peers_list: peers_list.remove(ticker)
                        top_peers = peers_list[:num_peers]
                        print(f"[Financial Tool] Đã tìm thấy các đối thủ (từ Screener): {top_peers}")
                        return top_peers

            print(f"[Financial Tool] Không tìm thấy {ticker} trong Screener, chuyển sang phương án Listing...")
            listing = Listing()
            all_companies_df = listing.symbols_by_industries()
            if all_companies_df.empty: return []

            target_company_info_listing = all_companies_df[all_companies_df['symbol'] == ticker]
            if target_company_info_listing.empty: return []
            
            industry_name_listing = target_company_info_listing['icb_name3'].iloc[0]
            print(f"[Financial Tool] Ngành của {ticker} (từ Listing) là: '{industry_name_listing}'")

            peers_df_listing = all_companies_df[all_companies_df['icb_name3'] == industry_name_listing]
            peers_list_listing = peers_df_listing['symbol'].dropna().unique().tolist()
            
            if ticker in peers_list_listing: peers_list_listing.remove(ticker)
            
            top_peers_fallback = peers_list_listing[:num_peers]
            print(f"[Financial Tool] Đã tìm thấy các đối thủ (từ Listing, không có vốn hóa): {top_peers_fallback}")
            return top_peers_fallback

        except Exception as e:
            print(f"[Financial Tool] Lỗi nghiêm trọng khi tìm công ty cùng ngành: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _get_financial_ratios(self, ticker: str) -> dict:
        try:
            stock_info = Vnstock().stock(symbol=ticker, source="TCBS")
            
            ratios_df = stock_info.finance.ratio(report_range='yearly', is_all=False)
            if ratios_df.empty: return {"Ngành": "Không xác định"}
            
            ratios = ratios_df.iloc[0].to_dict()
            overview_df = stock_info.company.overview()
            industry = overview_df.get("industry", pd.Series(["Không xác định"])).iloc[0]
            
            pe = ratios.get("priceToEarnings")
            pb = ratios.get("priceToBook")
            roe = ratios.get("roe")
            margin = ratios.get("grossProfitMargin")
            return { "P/E": pe, "P/B": pb, "ROE": roe, "Biên LNG": margin, "Ngành": industry }
        except Exception as e:
            print(f"Không thể lấy dữ liệu cho {ticker}: {e}")
            return { "P/E": None, "P/B": None, "ROE": None, "Biên LNG": None, "Ngành": "Không xác định"}

    def _run(self, ticker: str) -> str:
        # Lớp phòng thủ JSON
        try:
            data = json.loads(ticker)
            if isinstance(data, dict) and 'ticker' in data: ticker = data['ticker']
        except (json.JSONDecodeError, TypeError): pass

        print(f"[Financial Tool] Bắt đầu phân tích toàn diện cho {ticker}...")
        main_company_data = self._get_financial_ratios(ticker)
        industry_name = main_company_data.get("Ngành", "Không xác định")
        
        report = f"### Phân tích Tài chính Nội tại & Cạnh tranh cho {ticker}\n\n"
        report += f"**Ngành:** {industry_name}\n\n"
        
        report += f"**Các chỉ số chính của {ticker} (dữ liệu năm gần nhất):**\n"

        def safe_format(value, format_spec):
            if value is None or not isinstance(value, (int, float)): return "N/A"
            return format(value, format_spec)

        report += f"- **P/E:** {safe_format(main_company_data.get('P/E'), '.2f')}\n"
        report += f"- **P/B:** {safe_format(main_company_data.get('P/B'), '.2f')}\n"
        report += f"- **ROE:** {safe_format(main_company_data.get('ROE'), '.2%')}\n"
        report += f"- **Biên lợi nhuận gộp:** {safe_format(main_company_data.get('Biên LNG'), '.2%')}\n\n"

        peers = self._get_industry_peers(ticker)
        if not peers:
            report += "**Phân tích Cạnh tranh:** Không tìm thấy công ty cùng ngành phù hợp để so sánh.\n"
            return report

        peer_data = {p: self._get_financial_ratios(p) for p in peers}
        all_data = {ticker: main_company_data, **peer_data}

        report += "**Bảng so sánh với các công ty cùng ngành:**\n\n"
        headers = ["Chỉ số", ticker] + peers
        report += "| " + " | ".join(headers) + " |\n"
        report += "| " + " | ".join(["---"] * len(headers)) + " |\n"
        
        metrics_to_compare = ["P/E", "P/B", "ROE", "Biên LNG"]
        for metric in metrics_to_compare:
            row = [f"**{metric}**"]
            for company in [ticker] + peers:
                value = all_data[company].get(metric)
                if metric in ["ROE", "Biên LNG"]: row.append(safe_format(value, '.2%'))
                else: row.append(safe_format(value, '.2f'))
            report += "| " + " | ".join(row) + " |\n"

        print(f"[Financial Tool] Phân tích cho {ticker} hoàn tất.")
        return report
