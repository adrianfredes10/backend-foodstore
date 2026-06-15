# queries de solo lectura para estadisticas del negocio
# usa text() de SQLAlchemy para DATE_TRUNC y agregaciones de PostgreSQL
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import List

from sqlalchemy import text
from sqlmodel import Session


class EstadisticasRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_resumen_kpis(self) -> dict:
        hoy = date.today()

        # ventas hoy: pedidos no cancelados creados hoy
        row_hoy = self.session.exec(
            text("""
                SELECT COALESCE(SUM(total), 0)
                FROM pedido p
                JOIN estado_pedido e ON p.estado_id = e.id
                WHERE DATE(p.created_at) = :hoy
                  AND e.codigo != 'CANCELADO'
            """),
            params={"hoy": hoy},
        ).one()
        ventas_hoy = Decimal(str(row_hoy[0]))

        # ticket promedio: pedidos del mes actual no cancelados
        row_ticket = self.session.exec(
            text("""
                SELECT COALESCE(AVG(p.total), 0)
                FROM pedido p
                JOIN estado_pedido e ON p.estado_id = e.id
                WHERE DATE_TRUNC('month', p.created_at) = DATE_TRUNC('month', CURRENT_DATE)
                  AND e.codigo != 'CANCELADO'
            """)
        ).one()
        ticket_promedio = Decimal(str(row_ticket[0]))

        # pedidos activos: no terminales
        row_activos = self.session.exec(
            text("""
                SELECT COUNT(*)
                FROM pedido p
                JOIN estado_pedido e ON p.estado_id = e.id
                WHERE e.es_terminal = false
            """)
        ).one()
        pedidos_activos = int(row_activos[0])

        # ingresos del mes
        row_mes = self.session.exec(
            text("""
                SELECT COALESCE(SUM(p.total), 0)
                FROM pedido p
                JOIN estado_pedido e ON p.estado_id = e.id
                WHERE DATE_TRUNC('month', p.created_at) = DATE_TRUNC('month', CURRENT_DATE)
                  AND e.codigo != 'CANCELADO'
            """)
        ).one()
        ingresos_mes = Decimal(str(row_mes[0]))

        return {
            "ventas_hoy": str(ventas_hoy.quantize(Decimal("0.01"))),
            "ticket_promedio": str(ticket_promedio.quantize(Decimal("0.01"))),
            "pedidos_activos": pedidos_activos,
            "ingresos_mes": str(ingresos_mes.quantize(Decimal("0.01"))),
        }

    def get_ventas_periodo(self, desde: date, hasta: date, agrupacion: str) -> List[dict]:
        # agrupacion: 'day' | 'week' | 'month'
        allowed = {"day", "week", "month"}
        if agrupacion not in allowed:
            agrupacion = "day"

        rows = self.session.exec(
            text(f"""
                SELECT
                    DATE_TRUNC('{agrupacion}', p.created_at)::date::text AS periodo,
                    COALESCE(SUM(p.total), 0) AS total_ventas,
                    COUNT(*) AS cantidad_pedidos
                FROM pedido p
                JOIN estado_pedido e ON p.estado_id = e.id
                WHERE p.created_at >= :desde
                  AND p.created_at < :hasta + INTERVAL '1 day'
                  AND e.codigo != 'CANCELADO'
                GROUP BY 1
                ORDER BY 1
            """),
            params={"desde": desde, "hasta": hasta},
        ).all()

        return [
            {
                "periodo": str(r[0]),
                "total_ventas": str(Decimal(str(r[1])).quantize(Decimal("0.01"))),
                "cantidad_pedidos": int(r[2]),
            }
            for r in rows
        ]

    def get_productos_top(self, limit: int = 10) -> List[dict]:
        # EST-02: usa subtotal_snap (snapshot inmutable, garantiza precios historicos)
        rows = self.session.exec(
            text("""
                SELECT
                    dp.nombre_snapshot,
                    COALESCE(SUM(dp.subtotal_snap), 0) AS ingresos,
                    SUM(dp.cantidad) AS cantidad_vendida
                FROM detalle_pedido dp
                JOIN pedido p ON dp.pedido_id = p.id
                JOIN estado_pedido e ON p.estado_id = e.id
                WHERE e.codigo != 'CANCELADO'
                GROUP BY dp.nombre_snapshot
                ORDER BY ingresos DESC
                LIMIT :limit
            """),
            params={"limit": limit},
        ).all()

        return [
            {
                "producto_nombre": r[0],
                "ingresos": str(Decimal(str(r[1])).quantize(Decimal("0.01"))),
                "cantidad_vendida": int(r[2]),
            }
            for r in rows
        ]

    def get_pedidos_por_estado(self) -> List[dict]:
        rows = self.session.exec(
            text("""
                SELECT e.codigo, COUNT(p.id) AS cantidad
                FROM estado_pedido e
                LEFT JOIN pedido p ON p.estado_id = e.id
                GROUP BY e.codigo
                ORDER BY MIN(e.orden)
            """)
        ).all()

        return [{"estado_codigo": r[0], "cantidad": int(r[1])} for r in rows]

    def get_ingresos_por_forma_pago(self, desde: date, hasta: date) -> List[dict]:
        # EST-03: solo pedidos no cancelados (sin tabla pago aun)
        rows = self.session.exec(
            text("""
                SELECT
                    fp.codigo,
                    COALESCE(SUM(p.total), 0) AS total,
                    COUNT(*) AS cantidad
                FROM pedido p
                JOIN forma_pago fp ON p.forma_pago_id = fp.id
                JOIN estado_pedido e ON p.estado_id = e.id
                WHERE p.created_at >= :desde
                  AND p.created_at < :hasta + INTERVAL '1 day'
                  AND e.codigo != 'CANCELADO'
                GROUP BY fp.codigo
                ORDER BY total DESC
            """),
            params={"desde": desde, "hasta": hasta},
        ).all()

        return [
            {
                "forma_pago_codigo": r[0],
                "total": str(Decimal(str(r[1])).quantize(Decimal("0.01"))),
                "cantidad": int(r[2]),
            }
            for r in rows
        ]
