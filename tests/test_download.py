import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories.book import BookRepository
from app.database.repositories.favorite import FavoriteRepository
from app.database.repositories.user import UserRepository
from app.services.download import DownloadService


@pytest.mark.asyncio
async def test_favorites_workflow(db_session: AsyncSession):
    """Test user adding and removing books from favorites."""
    user_repo = UserRepository(db_session)
    user, _ = await user_repo.get_or_create(
        telegram_id=555666777,
        first_name="FavUser"
    )

    book_repo = BookRepository(db_session)
    book = await book_repo.save_or_update(
        title="Favorite Test Book",
        source_name="manual",
        source_id="fav_test_1"
    )
    await db_session.commit()

    fav_repo = FavoriteRepository(db_session)

    # Initially not favorite
    assert await fav_repo.is_favorite(user.id, book.id) is False

    # Add to favorites
    added = await fav_repo.add_favorite(user.id, book.id)
    assert added is True
    assert await fav_repo.is_favorite(user.id, book.id) is True

    # Check favorites list
    favs, total = await fav_repo.get_user_favorites(user.id)
    assert total == 1
    assert favs[0].id == book.id

    # Remove from favorites
    removed = await fav_repo.remove_favorite(user.id, book.id)
    assert removed is True
    assert await fav_repo.is_favorite(user.id, book.id) is False


@pytest.mark.asyncio
async def test_download_cached_telegram_file_id(db_session: AsyncSession):
    """When telegram_file_id is already present, bot immediately sends file_id."""
    user_repo = UserRepository(db_session)
    user, _ = await user_repo.get_or_create(
        telegram_id=888999000,
        first_name="DownloadUser"
    )

    book_repo = BookRepository(db_session)
    book = await book_repo.save_or_update(
        title="Cached File Book",
        source_name="manual",
        source_id="cached_book_1",
        formats_data=[{
            "format": "pdf",
            "file_url": "https://example.com/cached.pdf",
            "telegram_file_id": "telegram_cached_file_id_xyz123"
        }]
    )
    await db_session.commit()

    format_obj = book.formats[0]
    mock_bot = MagicMock()
    mock_bot.send_document = AsyncMock()

    service = DownloadService()
    success, file_id, error = await service.deliver_file(
        bot=mock_bot,
        chat_id=888999000,
        user_id=user.id,
        book=book,
        format_obj=format_obj,
        session=db_session
    )

    assert success is True
    assert file_id == "telegram_cached_file_id_xyz123"
    assert error is None
    # Ensure send_document was called with telegram_file_id without downloading HTTP
    mock_bot.send_document.assert_called_once()
    assert mock_bot.send_document.call_args[1]["document"] == "telegram_cached_file_id_xyz123"


@pytest.mark.asyncio
async def test_download_file_exceeds_size_limit(db_session: AsyncSession):
    """Files exceeding 50MB should return size limit warning and not download."""
    user_repo = UserRepository(db_session)
    user, _ = await user_repo.get_or_create(
        telegram_id=444333222,
        first_name="BigFileUser"
    )

    book_repo = BookRepository(db_session)
    book = await book_repo.save_or_update(
        title="Huge Video/Book Archive",
        source_name="manual",
        source_id="huge_file_1",
        formats_data=[{
            "format": "pdf",
            "file_url": "https://example.com/huge.pdf"
        }]
    )
    await db_session.commit()

    format_obj = book.formats[0]
    mock_bot = MagicMock()

    # Mock HEAD response reporting 80 MB
    mock_head_res = MagicMock()
    mock_head_res.headers = {"content-length": str(80 * 1024 * 1024)}

    with patch("httpx.AsyncClient.head", new_callable=AsyncMock) as mock_head:
        mock_head.return_value = mock_head_res
        service = DownloadService()
        success, file_id, error = await service.deliver_file(
            bot=mock_bot,
            chat_id=444333222,
            user_id=user.id,
            book=book,
            format_obj=format_obj,
            session=db_session
        )

        assert success is False
        assert file_id is None
        assert error is not None
        assert "too_large" in error
