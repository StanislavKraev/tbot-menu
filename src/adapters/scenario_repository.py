# src/repositories/scenario_repository.py
from typing import Any
from sqlalchemy import select, insert, update, delete, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncEngine

from src.models.tables import scenarios
from src.models.schemas import (
    Scenario, GeneralLeadMagnitScenario,
    BackgroundReminderScenario, ScenarioType, SymptomGuide
)

# TODO: привести в порядок

class ScenarioRepository:
    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine
        self._type_map = {
            ScenarioType.GENERAL_LEAD_MAGNIT: GeneralLeadMagnitScenario,
            ScenarioType.BACKGROUND_REMINDER: BackgroundReminderScenario,
        }

    async def create_scenario(
            self,
            scenario: Scenario,
            scenario_id: str | None = None
    ) -> str:
        """
        Сохраняет сценарий. Если scenario_id не передан - генерирует из типа+версии.
        """
        # Генерируем ID если не указан
        business_id = scenario_id or scenario.get_scenario_id()

        async with self._engine.begin() as conn:
            # Проверяем уникальность business ID
            existing = await conn.execute(
                select(scenarios.c.pk).where(scenarios.c.scenario_id == business_id)
            )
            if existing.fetchone():
                raise ValueError(f"Scenario with id '{business_id}' already exists")

            # Сериализуем Pydantic -> dict (исключаем поля, которые вынесены в колонки)
            data = scenario.model_dump(
                exclude={"scenario_type", "title", "version", "is_active"}
            )

            stmt = insert(scenarios).values(
                scenario_id=business_id,
                scenario_type=scenario.scenario_type.value,
                title=scenario.title,
                version=scenario.version,
                is_active=scenario.is_active,
                data=data
            ).returning(scenarios.c.scenario_id)

            result = await conn.execute(stmt)
            return result.scalar_one()

    async def get_by_scenario_id(self, scenario_id: str) -> Scenario | None:
        """Получает сценарий по бизнес-ID (e.g., 'general_lm_v1')."""
        async with self._engine.begin() as conn:
            stmt = select(scenarios).where(scenarios.c.scenario_id == scenario_id)
            result = await conn.execute(stmt)
            row = result.fetchone()
            return self._deserialize_row(row) if row else None

    async def get_active_scenario_by_type(
            self,
            scenario_type: ScenarioType
    ) -> Scenario | None:
        """Получает активный сценарий по типу (последняя версия)."""
        async with self._engine.begin() as conn:
            stmt = (
                select(scenarios)
                .where(
                    and_(
                        scenarios.c.scenario_type == scenario_type.value,
                        scenarios.c.is_active == True
                    )
                )
                .order_by(scenarios.c.version.desc())
                .limit(1)
            )
            result = await conn.execute(stmt)
            row = result.fetchone()
            return self._deserialize_row(row) if row else None

    async def get_symptom_guide(
            self,
            scenario_id: str,
            symptom: str
    ) -> SymptomGuide | None:
        """Утилитарный метод: получает конкретный гайд из GeneralLeadMagnitScenario."""
        scenario = await self.get_by_scenario_id(scenario_id)

        if isinstance(scenario, GeneralLeadMagnitScenario):
            return scenario.get_guide_by_symptom(symptom)
        return None

    async def list_scenarios(
            self,
            scenario_type: ScenarioType | None = None,
            active_only: bool = True,
            limit: int = 100
    ) -> list[Scenario]:
        """Список сценариев с фильтрацией."""
        async with self._engine.begin() as conn:
            stmt = select(scenarios)

            if scenario_type:
                stmt = stmt.where(scenarios.c.scenario_type == scenario_type.value)
            if active_only:
                stmt = stmt.where(scenarios.c.is_active == True)

            stmt = stmt.order_by(scenarios.c.created_at.desc()).limit(limit)
            result = await conn.execute(stmt)

            return [self._deserialize_row(row) for row in result.fetchall()]

    async def update_scenario_data(
            self,
            scenario_id: str,
            new_scenario: Scenario
    ) -> None:
        """Обновляет сценарий (создает новую версию или заменяет текущую)."""
        async with self._engine.begin() as conn:
            data = new_scenario.model_dump(
                exclude={"scenario_type", "title", "version", "is_active"}
            )

            stmt = (
                update(scenarios)
                .where(scenarios.c.scenario_id == scenario_id)
                .values(
                    title=new_scenario.title,
                    is_active=new_scenario.is_active,
                    data=data,
                    updated_at=func.now()
                )
            )
            await conn.execute(stmt)

    def _deserialize_row(self, row: Any) -> Scenario:
        """Десериализация строки БД в конкретный Pydantic класс."""
        data = dict(row.data)

        # Восстанавливаем поля из колонок БД в объект
        data.update({
            "scenario_type": row.scenario_type,
            "title": row.title,
            "version": row.version,
            "is_active": row.is_active,
        })

        # Определяем класс по типу
        scenario_type = ScenarioType(row.scenario_type)
        model_class = self._type_map.get(scenario_type)

        if not model_class:
            raise ValueError(f"Unknown scenario type: {scenario_type}")

        return model_class(**data)