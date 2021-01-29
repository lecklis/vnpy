from typing import Dict, List
from matplotlib.pyplot import contour

import pyqtgraph as pg

from vnpy.trader.ui import QtCore, QtWidgets, QtGui
from vnpy.trader.engine import MainEngine
from vnpy.trader.constant import OptionType


from ..engine import OptionEngine


class OptionSpreadWidget(QtWidgets.QWidget):

    def __init__(self, option_engine: OptionEngine) -> None:
        super().__init__()

        self.option_engine: OptionEngine = option_engine
        self.main_engine: MainEngine = option_engine.main_engine

        self.init_ui()

    def init_ui(self) -> None:
        """"""
        self.setWindowTitle("期权价差")

        # Chart direction
        pg.setConfigOptions(antialias=True)

        graphics_window = pg.GraphicsWindow()
        self.spread_chart = graphics_window.addPlot(title="期权价差组合")
        self.spread_chart.showGrid(x=True, y=True)
        self.spread_chart.setLabel("left", "价差盈亏")
        self.spread_chart.setLabel("bottom", "标的价格")
        self.spread_chart.addLegend()
        self.spread_chart.setMenuEnabled(False)
        self.spread_chart.setMouseEnabled(False, False)

        color = (255, 255, 0)
        pen = pg.mkPen(color, width=2)
        self.spread_curve = self.spread_chart.plot(
            name="价差组合",
            pen=pen,
            symbolBrush=color
        )

        # Button and edit area
        self.leg_edits = []
        grid = QtWidgets.QGridLayout()

        for i in range(4):
            symbol_edit = QtWidgets.QLineEdit()
            pos_edit = QtWidgets.QLineEdit()
            self.leg_edits.append((symbol_edit, pos_edit))

            grid.addWidget(QtWidgets.QLabel(f"腿{i+1}"), i, 0)
            grid.addWidget(symbol_edit, i, 1)
            grid.addWidget(pos_edit, i, 2)

        self.start_edit = QtWidgets.QLineEdit()
        self.stop_edit = QtWidgets.QLineEdit()
        self.step_edit = QtWidgets.QLineEdit()
        button = QtWidgets.QPushButton("计算")
        button.clicked.connect(self.run_analysis)

        form = QtWidgets.QFormLayout()
        form.addRow("开始价格", self.start_edit)
        form.addRow("结束价格", self.stop_edit)
        form.addRow("价格步进", self.step_edit)
        form.addRow(button)

        vbox = QtWidgets.QVBoxLayout()
        vbox.addLayout(grid)
        vbox.addLayout(form)

        hbox = QtWidgets.QHBoxLayout()
        hbox.addLayout(vbox)
        hbox.addWidget(graphics_window)
        self.setLayout(hbox)

    def calculate_leg_pnl(self, vt_symbol: str, pos: int, underlying_price: float) -> float:
        """"""
        contract = self.main_engine.get_contract(vt_symbol)
        tick = self.main_engine.get_tick(vt_symbol)

        if contract.option_type == OptionType.CALL:
            pnl = max(underlying_price - contract.option_strike, 0) - tick.last_price
        elif contract.option_type == OptionType.PUT:
            pnl = max(contract.option_strike - underlying_price, 0) - tick.last_price
        else:
            pnl = underlying_price - tick.last_price

        pnl = pnl * contract.size * pos
        return pnl

    def calculate_spread_pnl(self, spread_pos: Dict[str, int], underlying_price: int) -> float:
        """"""
        spread_pnl = 0

        for vt_symbol, pos in spread_pos.items():
            leg_pnl = self.calculate_leg_pnl(vt_symbol, pos, underlying_price)
            spread_pnl += leg_pnl

        return spread_pnl

    def show_spread_pnls(self, spread_pos: Dict[str, int], underlying_prices: List[float]) -> list:
        """"""
        spread_pnls = [self.calculate_spread_pnl(spread_pos, p) for p in underlying_prices]
        self.spread_curve.setData(y=spread_pnls, x=underlying_prices)

    def run_analysis(self) -> None:
        """"""
        spread_pos = {}

        for tp in self.leg_edits:
            symbol_edit, pos_edit = tp
            vt_symbol = symbol_edit.text()
            if not vt_symbol:
                continue

            pos = int(pos_edit.text())
            spread_pos[vt_symbol] = pos

        start_text = self.start_edit.text()
        stop_text = self.stop_edit.text()
        step_text = self.step_edit.text()

        if not start_text or not stop_text or not step_text:
            return

        underlying_prices = list(range(
            int(start_text),
            int(stop_text),
            int(step_text),
        ))

        self.show_spread_pnls(spread_pos, underlying_prices)
