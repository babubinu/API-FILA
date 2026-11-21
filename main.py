from datetime import datetime
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(
    title="API da Fila de Atendimento",
    description="API para totem de fila de atendimento presencial.",
    version="1.0.0",
)


class ClienteIn(BaseModel):
    nome: str = Field(..., min_length=1, max_length=20, examples=["Maria"])
    tipo: Literal["N", "P"] = Field(..., description="N = normal, P = prioritário")


class Cliente(BaseModel):
    posicao: int
    nome: str
    tipo: Literal["N", "P"]
    data_chegada: datetime
    atendido: bool = False


# "Banco de dados" em memória
fila: list[Cliente] = []
atendidos: list[Cliente] = []


def renumerar() -> None:
    """Recalcula a posição de todos na fila (1, 2, 3...)."""
    for i, cliente in enumerate(fila, start=1):
        cliente.posicao = i


@app.get("/fila")
def listar_fila():
    return [
        {
            "posicao": c.posicao,
            "nome": c.nome,
            "tipo": c.tipo,
            "data_chegada": c.data_chegada,
        }
        for c in fila
    ]


@app.get("/fila/{id}")
def buscar_cliente(id: int):
    for c in fila:
        if c.posicao == id:
            return {
                "posicao": c.posicao,
                "nome": c.nome,
                "tipo": c.tipo,
                "data_chegada": c.data_chegada,
            }
    raise HTTPException(status_code=404, detail=f"Não há cliente na posição {id} da fila.")


@app.post("/fila", status_code=201)
def adicionar_cliente(dados: ClienteIn):
    novo = Cliente(
        posicao=0,
        nome=dados.nome,
        tipo=dados.tipo,
        data_chegada=datetime.now(),
        atendido=False,
    )

    if novo.tipo == "P":
        # Prioritário entra depois do último prioritário já na fila
        idx = 0
        for i, c in enumerate(fila):
            if c.tipo == "P":
                idx = i + 1
        fila.insert(idx, novo)
    else:
        fila.append(novo)

    renumerar()
    return novo


@app.put("/fila")
def chamar_proximo():
    if not fila:
        raise HTTPException(status_code=404, detail="A fila está vazia.")

    atendido = fila.pop(0)
    atendido.posicao = 0
    atendido.atendido = True
    atendidos.append(atendido)

    renumerar()  # todos os demais andam uma posição (-1)
    return {"mensagem": "Fila atualizada.", "atendido": atendido, "fila": fila}


@app.delete("/fila/{id}")
def remover_cliente(id: int):
    for i, c in enumerate(fila):
        if c.posicao == id:
            removido = fila.pop(i)
            renumerar()
            return {"mensagem": "Cliente removido da fila.", "removido": removido}
    raise HTTPException(status_code=404, detail=f"Não há cliente na posição {id} da fila.")
