"""Persistência em SQLite (arquivo local; volume Docker em produção)."""
import json
import random
import secrets
import sqlite3
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS analises (
    id TEXT PRIMARY KEY,
    criado_em TEXT NOT NULL,
    entrada TEXT NOT NULL,
    resultado TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS relatos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    protocolo TEXT UNIQUE NOT NULL,
    criado_em TEXT NOT NULL,
    atualizado_em TEXT NOT NULL,
    descricao TEXT NOT NULL,
    bairro TEXT NOT NULL,
    cidade TEXT,
    cep TEXT,
    categoria TEXT NOT NULL,
    detalhe_outro TEXT,
    urgencia TEXT NOT NULL,
    categoria_ia TEXT NOT NULL,
    urgencia_ia TEXT NOT NULL,
    orgao_responsavel TEXT NOT NULL,
    resumo TEXT NOT NULL,
    orientacoes TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'recebido',
    nota_gestor TEXT,
    feedback_util INTEGER,
    feedback_comentario TEXT,
    demo INTEGER NOT NULL DEFAULT 0
);
"""


def _agora() -> datetime:
    return datetime.now(timezone.utc)


# Colunas adicionadas depois da 1ª versão: bancos antigos recebem ALTER TABLE no init().
COLUNAS_NOVAS = {"cidade": "TEXT", "detalhe_outro": "TEXT"}


def _row(row: sqlite3.Row) -> dict:
    from app.providers.canais import canal_para  # import local: canais depende de schemas

    d = dict(row)
    d["canal_oficial"] = canal_para(d.get("cidade")).model_dump()
    d["orientacoes"] = json.loads(d["orientacoes"])
    d["demo"] = bool(d["demo"])
    d["feedback_util"] = None if d["feedback_util"] is None else bool(d["feedback_util"])
    d["corrigido_pelo_cidadao"] = d["categoria"] != d["categoria_ia"] or d["urgencia"] != d["urgencia_ia"]
    return d


class Repository:
    def __init__(self, path: str):
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row

    def init(self) -> None:
        with self._lock, self._conn:
            self._conn.executescript(SCHEMA)
            existentes = {r["name"] for r in self._conn.execute("PRAGMA table_info(relatos)")}
            for coluna, tipo in COLUNAS_NOVAS.items():
                if coluna not in existentes:
                    self._conn.execute(f"ALTER TABLE relatos ADD COLUMN {coluna} {tipo}")

    # ----- análises pendentes (aguardando confirmação do cidadão) -----
    def save_analysis(self, analise_id: str, entrada: dict, resultado: dict) -> None:
        limite = (_agora() - timedelta(days=1)).isoformat()
        with self._lock, self._conn:
            # Minimização: análises não confirmadas somem depois de 24h.
            self._conn.execute("DELETE FROM analises WHERE criado_em < ?", (limite,))
            self._conn.execute(
                "INSERT INTO analises VALUES (?,?,?,?)",
                (analise_id, _agora().isoformat(), json.dumps(entrada, ensure_ascii=False),
                 json.dumps(resultado, ensure_ascii=False)),
            )

    def pop_analysis(self, analise_id: str) -> tuple[dict, dict] | None:
        with self._lock, self._conn:
            row = self._conn.execute("SELECT entrada, resultado FROM analises WHERE id=?", (analise_id,)).fetchone()
            if not row:
                return None
            self._conn.execute("DELETE FROM analises WHERE id=?", (analise_id,))
        return json.loads(row["entrada"]), json.loads(row["resultado"])

    # ----- relatos -----
    def create_report(self, entrada: dict, analise: dict, categoria: str, urgencia: str, demo: bool = False,
                      criado_em: datetime | None = None, status: str = "recebido",
                      feedback_util: bool | None = None, detalhe_outro: str | None = None) -> dict:
        quando = (criado_em or _agora()).isoformat()
        protocolo = f"ZL-{(criado_em or _agora()):%Y%m%d}-{secrets.token_hex(3).upper()}"
        with self._lock, self._conn:
            self._conn.execute(
                """INSERT INTO relatos (protocolo, criado_em, atualizado_em, descricao, bairro, cidade, cep, categoria,
                   detalhe_outro, urgencia, categoria_ia, urgencia_ia, orgao_responsavel, resumo, orientacoes,
                   status, feedback_util, demo) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (protocolo, quando, quando, entrada["descricao"], entrada["bairro"], entrada.get("cidade"),
                 entrada.get("cep"), categoria, detalhe_outro if categoria == "outro" else None, urgencia, analise["categoria"], analise["urgencia"], analise["orgao_responsavel"],
                 analise["resumo"], json.dumps(analise["orientacoes"], ensure_ascii=False), status,
                 None if feedback_util is None else int(feedback_util), int(demo)),
            )
        return self.get_by_protocols([protocolo])[0]

    def get_by_protocols(self, protocolos: list[str]) -> list[dict]:
        if not protocolos:
            return []
        marcadores = ",".join("?" * len(protocolos))
        with self._lock:
            rows = self._conn.execute(
                f"SELECT * FROM relatos WHERE protocolo IN ({marcadores}) ORDER BY criado_em DESC", protocolos
            ).fetchall()
        return [_row(r) for r in rows]

    def list_reports(self, limit: int = 1000) -> list[dict]:
        with self._lock:
            rows = self._conn.execute("SELECT * FROM relatos ORDER BY criado_em DESC LIMIT ?", (limit,)).fetchall()
        return [_row(r) for r in rows]

    def set_feedback(self, protocolo: str, util: bool, comentario: str | None) -> dict | None:
        with self._lock, self._conn:
            cur = self._conn.execute(
                "UPDATE relatos SET feedback_util=?, feedback_comentario=?, atualizado_em=? WHERE protocolo=?",
                (int(util), comentario, _agora().isoformat(), protocolo),
            )
        return self.get_by_protocols([protocolo])[0] if cur.rowcount else None

    def set_status(self, report_id: int, status: str, nota: str | None) -> dict | None:
        with self._lock, self._conn:
            cur = self._conn.execute(
                "UPDATE relatos SET status=?, nota_gestor=COALESCE(?, nota_gestor), atualizado_em=? WHERE id=?",
                (status, nota, _agora().isoformat(), report_id),
            )
            if not cur.rowcount:
                return None
            row = self._conn.execute("SELECT * FROM relatos WHERE id=?", (report_id,)).fetchone()
        return _row(row)

    def count(self) -> int:
        with self._lock:
            return self._conn.execute("SELECT COUNT(*) FROM relatos").fetchone()[0]

    def seed_demo(self, n: int = 60) -> None:
        """Relatos FICTÍCIOS (marcados como demo) para o painel não começar vazio."""
        from app.providers.llm import ORGAOS  # import local para evitar ciclo

        rnd = random.Random(42)
        bairros = ["Centro", "Presidente Altino", "Rochdale", "Km 18", "Jardim Veloso", "Vila Yara", "Bela Vista", "Quitaúna"]  # Osasco
        categorias = list(ORGAOS)
        urgencias = ["baixa", "media", "alta", "critica"]
        for _ in range(n):
            cat = rnd.choice(categorias)
            urg = rnd.choices(urgencias, weights=[3, 4, 2, 1])[0]
            dias = rnd.randint(0, 29)
            criado = _agora() - timedelta(days=dias, hours=rnd.randint(0, 23))
            if dias > 15 and rnd.random() < 0.7:
                status = "resolvido"
            else:
                status = rnd.choice(["recebido", "em_analise", "encaminhado", "recebido"])
            cat_ia, urg_ia = cat, urg
            if rnd.random() < 0.15:  # simula correções feitas pelo cidadão
                cat_ia = rnd.choice(categorias)
            analise = {"categoria": cat_ia, "urgencia": urg_ia, "orgao_responsavel": ORGAOS[cat],
                       "resumo": f"Relato fictício de demonstração: {cat.replace('_', ' ')}.",
                       "orientacoes": ["Relato de demonstração."]}
            entrada = {"descricao": "Relato fictício gerado para demonstração do painel.",
                       "bairro": rnd.choice(bairros), "cidade": "Osasco", "cep": None}
            self.create_report(entrada, analise, cat, urg, demo=True, criado_em=criado, status=status,
                               feedback_util=rnd.choice([True, True, True, False, None]))
