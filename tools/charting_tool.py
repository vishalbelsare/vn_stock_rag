# tools/charting_tool.py

import os
import traceback
import pandas as pd
from datetime import datetime, timedelta
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mplfinance as mpf

try:
    from crewai.tools import BaseTool
except Exception:
    class BaseTool:
        pass

try:
    from vnstock import Listing, Trading, Vnstock
except Exception:
    Listing = None
    Trading = None
    Vnstock = None

CHARTS_DIR = "charts"
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CHARTS_DIR_FULL_PATH = os.path.join(PROJECT_ROOT, CHARTS_DIR)
os.makedirs(CHARTS_DIR_FULL_PATH, exist_ok=True)


class ChartingTool(BaseTool):
    name: str = "Công cụ Vẽ Biểu đồ Chứng khoán Chuyên nghiệp"
    description: str = (
        "Tạo snapshot VN-Index + biểu đồ nến 3 tháng (SMA20 & SMA50) cho 1 mã cổ phiếu.\n"
        "Biểu đồ: không có grid, có chú thích giá đóng gần nhất, lưu file PNG vào thư mục charts."
    )

    def _get_vnindex_quote(self, stock_module):
        """Fetch recent VN-Index quote (last up to 5 days). Return DataFrame or None."""
        try:
            end = datetime.now()
            start = end - timedelta(days=5)
            if stock_module is not None and hasattr(stock_module, "stock"):
                try:
                    q = stock_module.stock(symbol='VNINDEX', source='VCI').quote.history(
                        start=start.strftime('%Y-%m-%d'),
                        end=end.strftime('%Y-%m-%d')
                    )
                    if isinstance(q, pd.DataFrame) and not q.empty:
                        return q
                except Exception:
                    traceback.print_exc()
            return None
        except Exception:
            traceback.print_exc()
            return None

    def _get_history_df(self, stock_module, ticker: str, start_date: datetime, end_date: datetime):
        """
        Try multiple ways to fetch history. Normalize to DataFrame indexed by datetime
        with columns Open, High, Low, Close, (optional) Volume.
        """
        try:
            df = None
            if stock_module is not None and hasattr(stock_module, "stock"):
                try:
                    df = stock_module.stock(symbol=ticker, source='TCBS').quote.history(
                        start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d')
                    )
                except Exception:
                    try:
                        df = stock_module.stock(symbol=ticker).quote.history(
                            start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d')
                        )
                    except Exception:
                        traceback.print_exc()
                        df = None

            if (df is None or (hasattr(df, "empty") and df.empty)) and Trading is not None:
                try:
                    t = Trading()
                    if hasattr(t, "history"):
                        df = t.history(ticker, start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'))
                    elif hasattr(t, "historical_price"):
                        df = t.historical_price(ticker, start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'))
                except Exception:
                    traceback.print_exc()
                    df = None

            if df is None:
                return None

            if not isinstance(df, pd.DataFrame):
                try:
                    df = pd.DataFrame(df)
                except Exception:
                    return None

            time_candidates = ['time', 'datetime', 'date']
            time_col = None
            for c in time_candidates:
                if c in df.columns:
                    time_col = c
                    break
            if time_col is None and isinstance(df.index, pd.DatetimeIndex):
                pass
            elif time_col is None:
                for c in df.columns:
                    if 'time' in c.lower() or 'date' in c.lower():
                        time_col = c
                        break

            if time_col:
                try:
                    df[time_col] = pd.to_datetime(df[time_col], errors='coerce')
                    df.set_index(time_col, inplace=True)
                except Exception:
                    pass

            col_map = {}
            mapping_candidates = {
                'Open': ['open', 'Open', 'o', 'start'],
                'High': ['high', 'High', 'h'],
                'Low':  ['low', 'Low', 'l'],
                'Close':['close', 'Close', 'c', 'last', 'price'],
                'Volume':['volume', 'Volume', 'vol']
            }
            for target, candidates in mapping_candidates.items():
                for c in candidates:
                    if c in df.columns:
                        col_map[c] = target
                        break
            if col_map:
                try:
                    df.rename(columns=col_map, inplace=True)
                except Exception:
                    pass

            required = {'Open', 'High', 'Low', 'Close'}
            if not required.issubset(set(df.columns)):
                numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
                if len(numeric_cols) >= 4:
                    try:
                        df['Open'] = pd.to_numeric(df[numeric_cols[0]], errors='coerce')
                        df['High'] = pd.to_numeric(df[numeric_cols[1]], errors='coerce')
                        df['Low']  = pd.to_numeric(df[numeric_cols[2]], errors='coerce')
                        df['Close']= pd.to_numeric(df[numeric_cols[3]], errors='coerce')
                    except Exception:
                        pass
                else:
                    return None

            keep_cols = ['Open', 'High', 'Low', 'Close']
            if 'Volume' in df.columns:
                keep_cols.append('Volume')

            df = df[keep_cols].copy()

            df = df[~df.index.isna()]
            df = df[df['Close'].notna()]
            if df.empty:
                return None

            try:
                df = df.sort_index()
            except Exception:
                pass

            return df

        except Exception:
            traceback.print_exc()
            return None

    def _run(self, ticker: str) -> str:
        """
        Main function:
        - ticker: stock symbol (string)
        - Uses today's date as end_date, start_date = end_date - 365 days
        - Returns Markdown text and saves PNG into charts/
        """
        try:
            ticker = str(ticker).upper().strip()
            print(f"[Charting Tool] Bắt đầu tạo biểu đồ cho {ticker}...")

            try:
                listing_module = Listing() if Listing is not None else None
            except Exception:
                listing_module = None
            try:
                trading_module = Trading() if Trading is not None else None
            except Exception:
                trading_module = None
            try:
                stock_module = Vnstock() if Vnstock is not None else None
            except Exception:
                stock_module = None

            vnindex_quote = self._get_vnindex_quote(stock_module)
            if vnindex_quote is None or (hasattr(vnindex_quote, "empty") and vnindex_quote.empty):
                market_snapshot_md = "### I. Tổng Quan Thị Trường Phiên Gần Nhất\n\nKhông thể tải dữ liệu VN-Index.\n\n"
            else:
                try:
                    latest = vnindex_quote.iloc[-1]
                    open_v = latest.get('open') if 'open' in latest.index else latest.get('Open', None)
                    close_v = latest.get('close') if 'close' in latest.index else latest.get('Close', None)
                    vol_v = latest.get('volume') if 'volume' in latest.index else latest.get('Volume', None)
                    if open_v is None or close_v is None:
                        market_snapshot_md = "### I. Tổng Quan Thị Trường Phiên Gần Nhất\n\nDữ liệu VN-Index không đầy đủ (open/close).\n\n"
                    else:
                        try:
                            vn_change = float(close_v) - float(open_v)
                            vn_pct = (vn_change / float(open_v)) * 100 if float(open_v) != 0 else 0.0
                        except Exception:
                            vn_change = 0.0
                            vn_pct = 0.0
                        try:
                            vol_display = f"{int(vol_v):,}" if (vol_v is not None and not pd.isna(vol_v)) else "N/A"
                        except Exception:
                            vol_display = "N/A"
                        market_snapshot_md = (
                            "### I. Tổng Quan Thị Trường Phiên Gần Nhất\n\n"
                            f"- **VN-Index:** {float(close_v):.2f} điểm ({vn_change:+.2f} điểm, {vn_pct:+.2f}%)\n"
                            f"- **Khối lượng:** {vol_display} cổ phiếu\n\n"
                        )
                except Exception:
                    traceback.print_exc()
                    market_snapshot_md = "### I. Tổng Quan Thị Trường Phiên Gần Nhất\n\nKhông thể phân tích dữ liệu VN-Index.\n\n"

            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)

            hist_df = self._get_history_df(stock_module, ticker, start_date, end_date)
            if hist_df is None or hist_df.empty:
                return f"Đã xảy ra lỗi khi tạo biểu đồ cho mã '{ticker}': Không tìm thấy dữ liệu lịch sử đủ để vẽ biểu đồ.\n\n{market_snapshot_md}"

            try:
                mc = mpf.make_marketcolors(up='g', down='r', inherit=True)
                style = mpf.make_mpf_style(marketcolors=mc, gridstyle='', rc={'axes.grid': False})

                chart_filename = f"{ticker}_{end_date.strftime('%Y%m%d')}.png"
                chart_filepath_full = os.path.join(CHARTS_DIR_FULL_PATH, chart_filename)
                chart_filepath_relative = os.path.join(CHARTS_DIR, chart_filename).replace("\\", "/")

                title_str = f"{ticker} — {start_date.strftime('%Y-%m-%d')} ➜ {end_date.strftime('%Y-%m-%d')}"
                subtitle = "Biểu đồ 12 tháng (SMA20, SMA50)."

                volume_flag = 'Volume' in hist_df.columns

                fig, axes = mpf.plot(
                    hist_df,
                    type='candle',
                    style=style,
                    title=f"{title_str}\n{subtitle}",
                    ylabel='Giá (VND)',
                    mav=(20, 50),
                    volume=volume_flag,
                    returnfig=True,
                    figscale=1.2,
                    figratio=(12, 6),
                    tight_layout=True
                )

                main_ax = axes[0] if isinstance(axes, (list, tuple)) else axes

                try:
                    last_dt = hist_df.index[-1]
                    last_close = float(hist_df['Close'].iloc[-1])
                    main_ax.annotate(
                        f"{last_close:,.0f}",
                        xy=(last_dt, last_close),
                        xytext=(0.98, 0.92),
                        textcoords='axes fraction',
                        arrowprops=dict(arrowstyle='->', color='black', lw=1),
                        ha='right',
                        va='top',
                        fontsize=10,
                        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="black", alpha=0.85)
                    )
                except Exception:
                    traceback.print_exc()

                try:
                    main_ax.grid(False)
                    for spine in main_ax.spines.values():
                        spine.set_linewidth(0.8)
                        spine.set_alpha(0.8)
                except Exception:
                    pass

                try:
                    fig.savefig(chart_filepath_full, dpi=150, bbox_inches='tight')
                except Exception:
                    plt.savefig(chart_filepath_full, dpi=150, bbox_inches='tight')
                finally:
                    try:
                        plt.close(fig)
                    except Exception:
                        plt.close('all')

            except Exception:
                traceback.print_exc()
                return f"Đã xảy ra lỗi khi vẽ biểu đồ cho mã '{ticker}'.\n\n{market_snapshot_md}"

            chart_md = (
                f"### II. Biểu Đồ Kỹ Thuật Cổ Phiếu {ticker}\n\n"
                f"- Khoảng thời gian: **{start_date.strftime('%Y-%m-%d')}** → **{end_date.strftime('%Y-%m-%d')}**\n\n"
                f"![Biểu đồ nến của {ticker}]({chart_filepath_relative})"
            )

            final_output = f"{market_snapshot_md}\n{chart_md}"
            return final_output

        except Exception:
            traceback.print_exc()
            return f"Đã xảy ra lỗi khi tạo biểu đồ cho mã '{ticker}'."

