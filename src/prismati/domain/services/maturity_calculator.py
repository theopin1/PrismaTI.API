from __future__ import annotations

import uuid
from dataclasses import dataclass

from prismati.domain.entities.answer import Answer
from prismati.domain.entities.dimension import Dimension
from prismati.domain.entities.question import Question, Alternative
from prismati.domain.entities.result import AssessmentResult, DimensionResult
from prismati.domain.enums.status import AnswerType, DiagnosticSufficiency


@dataclass
class _DimensionAccumulator:
    """Acumulador auxiliar de dados por dimensão durante o cálculo."""

    dimensao: Dimension
    total_perguntas: int = 0
    respostas_numericas: int = 0
    respostas_na: int = 0
    respostas_ns: int = 0
    soma_notas: float = 0.0
    perguntas_preenchidas: int = 0


class MaturityCalculator:
    """Serviço de domínio responsável pelo cálculo de maturidade de TI.

    Regras implementadas:
    - Pontuação individual: (nota / 4) * 100
    - Maturidade por dimensão: (soma_notas) / (qtd_respostas_numericas * 4) * 100
    - Se dimensão não tem respostas numéricas → maturidade = None (indisponível)
    - Maturidade geral: média aritmética das dimensões com resultado válido (não None)
    - Cobertura: respostas_numericas / (total_perguntas - na_justificadas) * 100
    - Preenchimento: perguntas_preenchidas / total_perguntas * 100
    - Suficiência:
        READY_FOR_REVIEW → cobertura >= 80% e todas as dimensões com resultado
        PRELIMINARY      → cobertura < 80% ou alguma dimensão sem resultado
        INSUFFICIENT_DATA → nenhuma resposta numérica
    - NA justificada: excluída do cálculo de cobertura
    - NS: reduz cobertura, não recebe nota
    - Nota zero é resposta numérica válida
    """

    def calculate(
        self,
        avaliacao_id: uuid.UUID,
        dimensions: list[Dimension],
        questions: list[Question],
        answers: list[Answer],
        alternatives_by_id: dict[uuid.UUID, Alternative],
    ) -> AssessmentResult:
        """Calcula o resultado completo de uma avaliação.

        Args:
            avaliacao_id: ID da avaliação sendo calculada.
            dimensions: Lista de dimensões da versão do questionário.
            questions: Lista de perguntas agrupadas (com alternativas já carregadas).
            answers: Lista de respostas salvas para esta avaliação.
            alternatives_by_id: Mapa alternativa_id → Alternative para lookup de pontuação.

        Returns:
            AssessmentResult com todos os campos calculados.
        """
        # Indexar perguntas por dimensão
        questions_by_dimension: dict[uuid.UUID, list[Question]] = {}
        for q in questions:
            questions_by_dimension.setdefault(q.dimensao_id, []).append(q)

        # Indexar respostas por pergunta_id
        answers_by_question: dict[uuid.UUID, Answer] = {a.pergunta_id: a for a in answers}

        # --- Calcular por dimensão ---
        dimension_results: list[DimensionResult] = []
        total_perguntas_global = 0
        perguntas_preenchidas_global = 0
        respostas_numericas_global = 0
        respostas_na_global = 0

        for dim in dimensions:
            dim_questions = questions_by_dimension.get(dim.id, [])
            acc = _DimensionAccumulator(dimensao=dim, total_perguntas=len(dim_questions))
            total_perguntas_global += len(dim_questions)

            for q in dim_questions:
                answer = answers_by_question.get(q.id)
                if answer is None:
                    # Pergunta não respondida
                    continue

                acc.perguntas_preenchidas += 1
                perguntas_preenchidas_global += 1

                if answer.tipo_resposta == AnswerType.SCORED:
                    if answer.alternativa_id is None:
                        continue
                    alt = alternatives_by_id.get(answer.alternativa_id)
                    if alt is None:
                        continue
                    acc.respostas_numericas += 1
                    respostas_numericas_global += 1
                    acc.soma_notas += alt.pontuacao

                elif answer.tipo_resposta == AnswerType.NOT_APPLICABLE:
                    # NA justificada: excluída do cálculo, mas conta como preenchida
                    acc.respostas_na += 1
                    respostas_na_global += 1

                elif answer.tipo_resposta == AnswerType.NOT_KNOWN:
                    # NS: reduz cobertura, não recebe nota
                    acc.respostas_ns += 1

            # Calcular maturidade da dimensão
            if acc.respostas_numericas > 0:
                maturidade_dim = (acc.soma_notas / (acc.respostas_numericas * 4)) * 100
            else:
                maturidade_dim = None  # Indisponível, não é zero

            dimension_results.append(
                DimensionResult(
                    dimensao_id=dim.id,
                    dimensao_nome=dim.nome,
                    dimensao_codigo=dim.codigo,
                    total_perguntas=acc.total_perguntas,
                    respostas_numericas=acc.respostas_numericas,
                    respostas_na=acc.respostas_na,
                    respostas_ns=acc.respostas_ns,
                    soma_notas=acc.soma_notas,
                    maturidade=maturidade_dim,
                )
            )

        # --- Maturidade geral: média das dimensões com resultado válido ---
        dims_com_resultado = [dr for dr in dimension_results if dr.maturidade is not None]
        if dims_com_resultado:
            maturidade_geral: float | None = sum(dr.maturidade for dr in dims_com_resultado) / len(dims_com_resultado)
        else:
            maturidade_geral = None

        # --- Cobertura ---
        # Denominador: total_perguntas - respostas_NA_justificadas
        denominador_cobertura = total_perguntas_global - respostas_na_global
        if denominador_cobertura > 0:
            cobertura = (respostas_numericas_global / denominador_cobertura) * 100
        else:
            cobertura = 0.0

        # --- Preenchimento ---
        if total_perguntas_global > 0:
            preenchimento = (perguntas_preenchidas_global / total_perguntas_global) * 100
        else:
            preenchimento = 0.0

        # --- Suficiência ---
        suficiencia = self._calc_sufficiency(
            respostas_numericas_global=respostas_numericas_global,
            cobertura=cobertura,
            dimension_results=dimension_results,
        )

        return AssessmentResult(
            avaliacao_id=avaliacao_id,
            total_perguntas=total_perguntas_global,
            perguntas_preenchidas=perguntas_preenchidas_global,
            respostas_numericas=respostas_numericas_global,
            maturidade_geral=maturidade_geral,
            cobertura=round(cobertura, 2),
            preenchimento=round(preenchimento, 2),
            suficiencia=suficiencia,
            dimensoes=dimension_results,
        )

    @staticmethod
    def _calc_sufficiency(
        respostas_numericas_global: int,
        cobertura: float,
        dimension_results: list[DimensionResult],
    ) -> DiagnosticSufficiency:
        """Determina a suficiência do diagnóstico conforme as regras de negócio."""
        if respostas_numericas_global == 0:
            return DiagnosticSufficiency.INSUFFICIENT_DATA

        all_dimensions_have_score = all(dr.maturidade is not None for dr in dimension_results)

        if cobertura >= 80.0 and all_dimensions_have_score:
            return DiagnosticSufficiency.READY_FOR_REVIEW

        return DiagnosticSufficiency.PRELIMINARY

    @staticmethod
    def individual_score(pontuacao: int) -> float:
        """Calcula a pontuação percentual individual de uma alternativa (0-4 → 0-100%)."""
        return (pontuacao / 4) * 100
