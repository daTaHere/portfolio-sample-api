import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Any, Callable, Dict, List, Generator, Tuple
from tests.utils import count_log_events

from app.services.feeds.feed_service import get_10_feeds
from app.exceptions.base import ServiceException
from app.models.post_detail_model import PostWithComments

from app.schemas.feed_schemas import PostWithCommentsSchema

DEFAULT_POST_DATA = [
    {
        "userId": 1,
        "id": 1,
        "title": "sunt aut facere repellat provident occaecati excepturi optio reprehenderit",
        "body": "quia et suscipit\nsuscipit recusandae consequuntur expedita et cum\nreprehenderit molestiae ut ut quas totam\nnostrum rerum est autem sunt rem eveniet architecto",
    },
    {
        "userId": 1,
        "id": 2,
        "title": "qui est esse",
        "body": "est rerum tempore vitae\nsequi sint nihil reprehenderit dolor beatae ea dolores neque\nfugiat blanditiis voluptate porro vel nihil molestiae ut reiciendis\nqui aperiam non debitis possimus qui neque nisi nulla",
    },
    {
        "userId": 1,
        "id": 3,
        "title": "ea molestias quasi exercitationem repellat qui ipsa sit aut",
        "body": "et iusto sed quo iure\nvoluptatem occaecati omnis eligendi aut ad\nvoluptatem doloribus vel accusantium quis pariatur\nmolestiae porro eius odio et labore et velit aut",
    },
    {
        "userId": 1,
        "id": 4,
        "title": "eum et est occaecati",
        "body": "ullam et saepe reiciendis voluptatem adipisci\nsit amet autem assumenda provident rerum culpa\nquis hic commodi nesciunt rem tenetur doloremque ipsam iure\nquis sunt voluptatem rerum illo velit",
    },
    {
        "userId": 1,
        "id": 5,
        "title": "nesciunt quas odio",
        "body": "repudiandae veniam quaerat sunt sed\nalias aut fugiat sit autem sed est\nvoluptatem omnis possimus esse voluptatibus quis\nest aut tenetur dolor neque",
    },
]
DEFAULT_COMMENT_DATA = [
    {
        "post_id": 1,
        "id": 1,
        "name": "id labore ex et quam laborum",
        "email": "Eliseo@gardner.biz",
        "body": "laudantium enim quasi est quidem magnam voluptate ipsam eos\ntempora quo necessitatibus\ndolor quam autem quasi\nreiciendis et nam sapiente accusantium",
    },
    {
        "post_id": 1,
        "id": 2,
        "name": "quo vero reiciendis velit similique earum",
        "email": "Jayne_Kuhic@sydney.com",
        "body": "est natus enim nihil est dolore omnis voluptatem numquam\net omnis occaecati quod ullam at\nvoluptatem error expedita pariatur\nnihil sint nostrum voluptatem reiciendis et",
    },
    {
        "post_id": 2,
        "id": 3,
        "name": "odio adipisci rerum aut animi",
        "email": "Nikita@garfield.biz",
        "body": "quia molestiae reprehenderit quasi aspernatur\naut expedita occaecati aliquam eveniet laudantium\nomnis quibusdam delectus saepe quia accusamus maiores nam est\ncum et ducimus et vero voluptates excepturi deleniti ratione",
    },
    {
        "post_id": 1,
        "id": 4,
        "name": "alias odio sit",
        "email": "Lew@alysha.tv",
        "body": "non et atque\noccaecati deserunt quas accusantium unde odit nobis qui voluptatem\nquia voluptas consequuntur itaque dolor\net qui rerum deleniti ut occaecati",
    },
    {
        "post_id": 5,
        "id": 5,
        "name": "vero eaque aliquid doloribus et culpa",
        "email": "Hayden@althea.biz",
        "body": "harum non quasi et ratione\ntempore iure ex voluptates in ratione\nharum architecto fugit inventore cupiditate\nvoluptates magni quo et",
    },
]
DEFAULT_COMMENT_COUNT_TABLE = {
    1: 3,
    2: 1,
    5: 1,
    3: 0,
    4: 0,
}


@pytest.fixture
def mock_get_data() -> Generator[MagicMock, None, None]:
    async_mock = AsyncMock()
    async_mock.side_effect = [DEFAULT_POST_DATA, DEFAULT_COMMENT_DATA]
    with patch("app.services.feeds.feed_service.get_data", async_mock):
        yield async_mock


@pytest.fixture
def mock_get_data_factory() -> Callable[[], tuple[Any, AsyncMock]]:
    """Return a function that can create a patched get_data mock with given data."""

    def _mock_get_data(
        *side_effect_data: List[Any],
    ) -> Tuple[MagicMock, AsyncMock]:
        async_mock = AsyncMock()
        async_mock.side_effect = list(side_effect_data)
        patcher = patch("app.services.feeds.feed_service.get_data", async_mock)
        patcher.start()
        return patcher, async_mock

    return _mock_get_data


@pytest.fixture
def mock_check_cache() -> Generator[MagicMock, None, None]:
    with patch("app.services.feeds.feed_service.check_cache") as mock_cache:
        yield mock_cache


@pytest.fixture
def mock_cache_set() -> Generator[MagicMock, None, None]:
    with patch("app.services.feeds.feed_service.cache_set") as mock_cache:
        yield mock_cache


@pytest.mark.asyncio
async def test_get_10_feeds_success(
    captured_logs, mock_get_data, mock_check_cache, mock_cache_set
):
    expected_comment_counts = DEFAULT_COMMENT_COUNT_TABLE
    _async_mock = mock_get_data
    mock_check_cache.return_value = None
    feeds = await get_10_feeds(start=0, limit=5)

    log_counts = count_log_events(captured_logs, "get_10_feeds")

    assert _async_mock.await_count == 2
    assert isinstance(feeds, List)
    assert all(isinstance(feed, PostWithComments) for feed in feeds)
    assert len(feeds) == 5
    for feed in feeds:
        feed_id = feed.id
        assert isinstance(feed.comments, List)
        assert len(feed.comments) == expected_comment_counts.get(feed_id)
        assert all(comment._postId == feed_id for comment in feed.comments)
    assert log_counts.get("FETCH_COUNTS")
    assert log_counts.get("FILTERED_COMMENTS")
    assert log_counts.get("SUCCESS")
    assert not log_counts.get("ERROR")


@pytest.mark.asyncio
async def test_get_10_feeds_success_with_factory(
    captured_logs, mock_get_data_factory, mock_check_cache, mock_cache_set
):

    expected_comment_counts = DEFAULT_COMMENT_COUNT_TABLE
    mock_check_cache.return_value = None
    _patcher, _async_mock = mock_get_data_factory(
        DEFAULT_POST_DATA, DEFAULT_COMMENT_DATA
    )
    feeds = await get_10_feeds(start=0, limit=5)
    _patcher.stop()

    log_counts = count_log_events(captured_logs, "get_10_feeds")

    assert _async_mock.await_count == 2
    assert isinstance(feeds, List)
    assert all(isinstance(feed, PostWithComments) for feed in feeds)
    assert len(feeds) == 5
    for feed in feeds:
        feed_id = feed.id
        assert isinstance(feed.comments, List)
        assert len(feed.comments) == expected_comment_counts.get(feed_id)
        assert all(comment._postId == feed_id for comment in feed.comments)
    assert log_counts.get("FETCH_COUNTS")
    assert log_counts.get("FILTERED_COMMENTS")
    assert log_counts.get("SUCCESS")
    assert not log_counts.get("ERROR")


@pytest.mark.parametrize(
    "post_data, comment_data",
    [
        ([], []),
        ([], DEFAULT_COMMENT_DATA),
    ],
)
@pytest.mark.asyncio
async def test_get_10_feeds_success_empty_response(
    captured_logs,
    mock_get_data_factory,
    mock_check_cache,
    mock_cache_set,
    post_data: List[Dict[str, Any]],
    comment_data: List[Dict[str, Any]],
):
    mock_check_cache.return_value = None
    _patcher, _async_mock = mock_get_data_factory(post_data, comment_data)
    feeds = await get_10_feeds(start=0, limit=5)
    _patcher.stop()

    log_counts = count_log_events(captured_logs, "get_10_feeds")

    assert _async_mock.await_count == 2
    assert isinstance(feeds, List)
    assert len(feeds) == 0
    assert log_counts.get("FETCH_COUNTS")
    assert log_counts.get("FILTERED_COMMENTS")
    assert log_counts.get("SUCCESS")
    assert not log_counts.get("ERROR")


@pytest.mark.parametrize(
    "mock_side_effect",
    [TypeError("Invalid data"), ValueError("Invalid data")],
)
@pytest.mark.asyncio
async def test_get_10_feeds_raises_service_exception(
    captured_logs,
    mock_get_data_factory,
    mock_check_cache,
    mock_side_effect: BaseException,
):
    mock_check_cache.return_value = None
    _patcher, _async_mock = mock_get_data_factory(
        DEFAULT_POST_DATA, DEFAULT_COMMENT_DATA
    )

    with patch(
        "app.services.feeds.feed_service.PostWithComments",
        side_effect=mock_side_effect,
    ):
        with pytest.raises(ServiceException) as exc_info:
            await get_10_feeds(start=0, limit=5)
        _patcher.stop()

    log_counts = count_log_events(captured_logs, "get_10_feeds")

    assert _async_mock.await_count == 2
    assert log_counts.get("FETCH_COUNTS")
    assert log_counts.get("FILTERED_COMMENTS")
    assert not log_counts.get("SUCCESS")
    assert log_counts.get("ERROR")
