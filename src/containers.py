from dependency_injector import containers, providers

from src.adapters.pdf_repository import PdfRepository
from src.adapters.state_storage import StateStorage
from src.adapters.user_repository import UserRepository
from src.bot_init import BotInitializer
from src.db_engine_factory import db_engine_factory
from src.services.pdf_service import PdfService
from src.services.user_service import UserService


class AppContainer(containers.DeclarativeContainer):
    """DI-контейнер приложения."""

    config = providers.Configuration()

    # Infrastructure
    db_engine = providers.Callable(
        db_engine_factory(),
        url=config.database_conn,
        pool_size=10,
        max_overflow=10,
        pool_pre_ping=True,
    )

    # Repositories
    user_repository = providers.Factory(UserRepository, engine=db_engine)

    pdf_repository = providers.Factory(PdfRepository, engine=db_engine)

    state_storage = providers.Factory(StateStorage, engine=db_engine)

    # Services
    user_service = providers.Factory(UserService, repository=user_repository)

    pdf_service = providers.Factory(PdfService, repository=pdf_repository)

    # Bot
    bot_initializer = providers.Singleton(
        BotInitializer,
        bot_token=config.bot_token,
        user_service=user_service,
        pdf_service=pdf_service,
        state_storage=state_storage,
    )
