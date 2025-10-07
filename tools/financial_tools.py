# tools/financial_tools.py

# --- Imports ---
from typing import Type, Optional
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from vnstock import Vnstock
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from googlesearch import search # Thư viện để tìm kiếm đối thủ

# --- Pydantic Input Schema (Đổi tên cho phù hợp hơn) ---
class StockTickerInput(BaseModel):
    """Input schema cho các tool cần mã cổ phiếu."""
    ticker: str = Field(..., description="Mã cổ phiếu cần phân tích, ví dụ: 'FPT'.")

# -----------------------------------------------------------------------------
# CÔNG CỤ 1: PHÂN TÍCH KỸ THUẬT (GIỮ NGUYÊN TỪ FILE GỐC CỦA BẠN)
# -----------------------------------------------------------------------------
class TechDataTool(BaseTool):
    name: str = "Công cụ tra cứu dữ liệu cổ phiếu phục vụ phân tích kĩ thuật."
    description: str = "Công cụ tra cứu dữ liệu cổ phiếu phục vụ phân tích kĩ thuật, cung cấp các chỉ số như SMA, EMA, RSI, MACD, Bollinger Bands, và vùng hỗ trợ/kháng cự."
    args_schema: Type[BaseModel] = StockTickerInput

    # Sửa đổi nhỏ: pydantic model yêu cầu `ticker`, nên ta đổi `argument` thành `ticker`
    def _run(self, ticker: str) -> str:
        try:
            stock = Vnstock().stock(symbol=ticker, source="TCBS")
            company = Vnstock().stock(symbol=ticker, source='TCBS').company

            full_name = company.profile().get("company_name").iloc[0]
            industry = company.overview().get("industry").iloc[0]
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365) # Lấy dữ liệu 1 năm để có SMA200
            price_data = stock.quote.history(
                start=start_date.strftime("%Y-%m-%d"),
                end=end_date.strftime("%Y-%m-%d"),
                interval="1D"  
            )
            
            if price_data.empty:
                return f"Không tìm thấy dữ liệu lịch sử cho cổ phiếu {ticker}"
            
            tech_data = self._calculate_indicators(price_data)
            support_resistance = self._find_support_resistance(price_data)
            
            # Lấy dữ liệu gần nhất một cách an toàn hơn
            current_price = price_data['close'].iloc[-1]
            current_volume = price_data['volume'].iloc[-1]
            
            # Lấy giá và khối lượng 4 phiên trước đó
            recent_prices = price_data['close'].iloc[-5:-1].reindex()
            recent_volumes = price_data['volume'].iloc[-5:-1].reindex()
            
            latest_indicators = tech_data.iloc[-1]
            
            result = f"""### Phân tích Kỹ thuật cho {ticker}\n
            **Tên công ty:** {full_name}
            **Ngành:** {industry}
            **Ngày phân tích:** {datetime.now().strftime('%Y-%m-%d')}
            **Giá hiện tại:** {(current_price*1000):,.0f} VND
            **Khối lượng giao dịch:** {current_volume:,.0f} cp

            **GIÁ ĐÓNG CỬA 4 PHIÊN GẦN NHẤT:**
            - T-1: {(recent_prices.iloc[-1]*1000):,.0f} VND (KL: {recent_volumes.iloc[-1]:,.0f} cp)
            - T-2: {(recent_prices.iloc[-2]*1000):,.0f} VND (KL: {recent_volumes.iloc[-2]:,.0f} cp)
            - T-3: {(recent_prices.iloc[-3]*1000):,.0f} VND (KL: {recent_volumes.iloc[-3]:,.0f} cp)
            - T-4: {(recent_prices.iloc[-4]*1000):,.0f} VND (KL: {recent_volumes.iloc[-4]:,.0f} cp)
            
            **CHỈ SỐ KỸ THUẬT:**
            - SMA (20): {(latest_indicators['SMA_20']*1000):,.0f}
            - SMA (50): {(latest_indicators['SMA_50']*1000):,.0f}
            - SMA (200): {(latest_indicators['SMA_200']*1000):,.0f}
            - EMA (12): {(latest_indicators['EMA_12']*1000):,.0f}
            - EMA (26): {(latest_indicators['EMA_26']*1000):,.0f}
            - RSI (14): {latest_indicators['RSI_14']:.2f}
            - MACD: {latest_indicators['MACD']:.2f} (Signal: {latest_indicators['MACD_Signal']:.2f}, Hist: {latest_indicators['MACD_Hist']:.2f})
            - Bollinger Bands (Upper/Middle/Lower): {(latest_indicators['BB_Upper']*1000):,.0f} / {(latest_indicators['BB_Middle']*1000):,.0f} / {(latest_indicators['BB_Lower']*1000):,.0f}

            **CHỈ SỐ KHỐI LƯỢNG:**
            - Khối lượng hiện tại: {current_volume:,.0f} cp
            - Trung bình 10 phiên: {latest_indicators['Volume_SMA_10']:,.0f} cp
            - Trung bình 20 phiên: {latest_indicators['Volume_SMA_20']:,.0f} cp
            - Tỷ lệ Khối lượng / Trung bình 20: {latest_indicators['Volume_Ratio_20']:.2f}
            - On-Balance Volume (OBV): {latest_indicators['OBV']:,.0f}
            
            **VÙNG HỖ TRỢ VÀ KHÁNG CỰ:**
            {support_resistance}
            
            **NHẬN ĐỊNH KỸ THUẬT:**
            {self._get_technical_analysis(latest_indicators, current_price)}
            """
            return result
            
        except Exception as e:
            return f"Lỗi khi lấy dữ liệu kỹ thuật cho {ticker}: {e}"
    
    def _calculate_indicators(self, df):
        data = df.copy().reset_index()
        data['SMA_20'] = data['close'].rolling(window=20).mean()
        data['SMA_50'] = data['close'].rolling(window=50).mean()
        data['SMA_200'] = data['close'].rolling(window=200).mean()
        data['EMA_12'] = data['close'].ewm(span=12, adjust=False).mean()
        data['EMA_26'] = data['close'].ewm(span=26, adjust=False).mean()
        data['MACD'] = data['EMA_12'] - data['EMA_26']
        data['MACD_Signal'] = data['MACD'].ewm(span=9, adjust=False).mean()
        data['MACD_Hist'] = data['MACD'] - data['MACD_Signal']
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss.replace(0, np.nan)
        data['RSI_14'] = 100 - (100 / (1 + rs))
        data['RSI_14'] = data['RSI_14'].fillna(50)
        data['BB_Middle'] = data['close'].rolling(window=20).mean()
        std_dev = data['close'].rolling(window=20).std()
        data['BB_Upper'] = data['BB_Middle'] + (std_dev * 2)
        data['BB_Lower'] = data['BB_Middle'] - (std_dev * 2)
        data['Volume_SMA_10'] = data['volume'].rolling(window=10).mean()
        data['Volume_SMA_20'] = data['volume'].rolling(window=20).mean()
        data['Volume_SMA_50'] = data['volume'].rolling(window=50).mean()
        data['Volume_Ratio_20'] = data['volume'] / data['Volume_SMA_20']
        
        # Sửa lỗi OBV
        data['OBV'] = (np.sign(data['close'].diff()) * data['volume']).fillna(0).cumsum()
        
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
                else:
                    clusters.append([level])
            return [np.mean(cluster) for cluster in clusters]
        
        resistance_levels = sorted([r for r in cluster_levels(resistance_levels, threshold) if r > current_price])[:3]
        support_levels = sorted([s for s in cluster_levels(support_levels, threshold) if s < current_price], reverse=True)[:3]
        
        result = "Vùng kháng cự:\n" + "".join([f"- R{i+1}: {level*1000:,.0f} VND\n" for i, level in enumerate(resistance_levels)])
        result += "\nVùng hỗ trợ:\n" + "".join([f"- S{i+1}: {level*1000:,.0f} VND\n" for i, level in enumerate(support_levels)])
        return result
    
    def _get_technical_analysis(self, indicators, current_price):
        analysis = []
        if current_price > indicators['SMA_200']: analysis.append("- Xu hướng dài hạn: TĂNG.")
        else: analysis.append("- Xu hướng dài hạn: GIẢM.")
        if current_price > indicators['SMA_50']: analysis.append("- Xu hướng trung hạn: TĂNG.")
        else: analysis.append("- Xu hướng trung hạn: GIẢM.")
        if indicators['RSI_14'] > 70: analysis.append("- RSI: Vùng QUÁ MUA, có thể điều chỉnh.")
        elif indicators['RSI_14'] < 30: analysis.append("- RSI: Vùng QUÁ BÁN, có thể hồi phục.")
        else: analysis.append(f"- RSI: TRUNG TÍNH ({indicators['RSI_14']:.2f}).")
        if indicators['MACD'] > indicators['MACD_Signal']: analysis.append("- MACD: Tín hiệu TÍCH CỰC (đường MACD trên đường Signal).")
        else: analysis.append("- MACD: Tín hiệu TIÊU CỰC (đường MACD dưới đường Signal).")
        return "\n".join(analysis)

# -----------------------------------------------------------------------------
# CÔNG CỤ 2: "SIÊU TOOL" PHÂN TÍCH TÀI CHÍNH & CẠNH TRANH
# -----------------------------------------------------------------------------
class ComprehensiveFinancialTool(BaseTool):
    name: str = "Công cụ Phân tích Tài chính và Cạnh tranh Toàn diện"
    description: str = (
        "Một công cụ mạnh mẽ, chỉ cần nhận mã cổ phiếu, sẽ tự động thực hiện hai việc: "
        "1. Phân tích tài chính nội tại của công ty đó. "
        "2. Tìm kiếm các đối thủ cạnh tranh và tạo ra một bảng so sánh các chỉ số tài chính quan trọng. "
        "Công cụ này trả về một báo cáo hoàn chỉnh dạng Markdown."
    )
    args_schema: type[BaseModel] = StockTickerInput

    def _get_competitors(self, ticker: str, industry: str, num_competitors: int = 2) -> list[str]:
        print(f"[Financial Tool] Đang tìm công ty cùng ngành với {ticker}...")
        try:
            query = f"công ty chứng khoán cùng ngành {industry} Việt Nam -{ticker}"
            competitors = set()
            search_results = list(search(query, num_results=15, lang="vi"))
            
            for url in search_results:
                words = url.upper().replace("-", " ").replace("_", " ").split('/')
                for word in words:
                    # Mã cổ phiếu thường là 3 ký tự, viết hoa và không phải mã index
                    if len(word) == 3 and word.isalpha() and word != ticker and not word.startswith('VN'):
                        competitors.add(word)
                        if len(competitors) >= num_competitors: break
                if len(competitors) >= num_competitors: break
            
            found = list(competitors)
            print(f"[Financial Tool] Đã tìm thấy: {found}")
            return found
        except Exception as e:
            print(f"[Financial Tool] Lỗi khi tìm đối thủ: {e}. Sử dụng danh sách dự phòng.")
            if 'Công nghệ' in industry: return ['CMG', 'ELC']
            if 'Thép' in industry: return ['NKG', 'HSG']
            return []

    def _get_financial_ratios(self, ticker: str) -> dict:
        try:
            stock = Vnstock().stock(symbol=ticker, source="TCBS")
            ratios = stock.finance.ratio(period="year").iloc[0]
            industry = stock.company.overview().get("industry", "Không xác định").iloc[0]
            return {
                "P/E": ratios.get("priceToEarning"),
                "P/B": ratios.get("priceToBook"),
                "ROE": ratios.get("roe"),
                "Biên LNG": ratios.get("grossProfitMargin"),
                "Ngành": industry
            }
        except Exception as e:
            print(f"Không thể lấy dữ liệu cho {ticker}: {e}")
            return { "P/E": None, "P/B": None, "ROE": None, "Biên LNG": None, "Ngành": "Không xác định"}

    def _run(self, ticker: str) -> str:
        print(f"[Financial Tool] Bắt đầu phân tích tài chính toàn diện cho {ticker}...")
        main_company_data = self._get_financial_ratios(ticker)
        industry = main_company_data.get("Ngành", "Không xác định")
        
        report = f"### Phân tích Tài chính Nội tại & Cạnh tranh cho {ticker}\n\n"
        report += f"**Ngành:** {industry}\n\n"
        report += f"**Các chỉ số chính của {ticker} (dữ liệu năm gần nhất):**\n"

        def safe_format(value, format_spec):
            if value is None or not isinstance(value, (int, float)):
                return "N/A"
            return format(value, format_spec)

        pe = main_company_data.get('P/E')
        pb = main_company_data.get('P/B')
        roe = main_company_data.get('ROE')
        margin = main_company_data.get('Biên LNG')
        
        report += f"- **P/E:** {safe_format(pe, '.2f')}\n"
        report += f"- **P/B:** {safe_format(pb, '.2f')}\n"
        report += f"- **ROE:** {safe_format(roe, '.2%')}\n"
        report += f"- **Biên lợi nhuận gộp:** {safe_format(margin, '.2%')}\n\n"

        competitors = self._get_competitors(ticker, industry)
        if not competitors:
            report += "**Phân tích Cạnh tranh:** Không tìm thấy đối thủ phù hợp để so sánh.\n"
            return report

        competitor_data = {comp: self._get_financial_ratios(comp) for comp in competitors}

        report += "**Bảng so sánh với các công ty cùng ngành:**\n\n"
        headers = ["Chỉ số", ticker] + competitors
        report += "| " + " | ".join(headers) + " |\n"
        report += "| " + " | ".join(["---"] * len(headers)) + " |\n"
        
        metrics_to_compare = ["P/E", "P/B", "ROE", "Biên LNG"]
        all_data = {ticker: main_company_data, **competitor_data}

        for metric in metrics_to_compare:
            row = [f"**{metric}**"]
            for company in [ticker] + competitors:
                value = all_data[company].get(metric)
                # Dùng lại hàm safe_format
                if metric in ["ROE", "Biên LNG"]:
                    row.append(safe_format(value, '.2%'))
                else:
                    row.append(safe_format(value, '.2f'))
            report += "| " + " | ".join(row) + " |\n"

        print(f"[Financial Tool] Phân tích cho {ticker} hoàn tất.")
        return report
