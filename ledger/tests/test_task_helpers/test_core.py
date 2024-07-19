from unittest.mock import MagicMock, patch

from django.test import TestCase

from ledger.task_helpers.core_helpers import (
    AlreadyQueued,
    enqueue_next_task,
    no_fail_chain,
)

MODULE_PATH = "ledger.task_helpers.core_helpers"


class CoreHelpersTest(TestCase):
    @patch(MODULE_PATH + ".enqueue_next_task")
    def test_no_fail_chain(self, mock_enqueue):
        @no_fail_chain
        def test_func(*args, **kwargs):
            raise Exception("Test exception")

        with self.assertRaises(Exception):
            test_func(chain=[])

        mock_enqueue.assert_called_once()

    @patch(MODULE_PATH + ".signature")
    def test_enqueue_next_task(self, mock_signature):
        # given
        mock_task1 = MagicMock()
        mock_task2 = MagicMock()
        chain = [mock_task1, mock_task2]

        mock_sig = MagicMock()
        mock_sig.kwargs = {}  # Set kwargs to an empty dictionary
        mock_signature.return_value = mock_sig
        # when
        enqueue_next_task(chain)
        # then
        mock_sig.apply_async.assert_called_once_with(priority=9)
        self.assertEqual(mock_sig.kwargs["chain"], [mock_task2])

    @patch(MODULE_PATH + ".signature")
    @patch(MODULE_PATH + ".logger")
    def test_enqueue_next_task_alreadyqueued(self, mock_logger, mock_signature):
        # given
        mock_task1 = MagicMock()
        mock_task2 = MagicMock()
        chain = [mock_task1, mock_task2]

        mock_sig = MagicMock()
        mock_sig.kwargs = {}  # Set kwargs to an empty dictionary
        mock_sig.apply_async.side_effect = AlreadyQueued(
            countdown=10
        )  # apply_async raises AlreadyQueued
        mock_signature.return_value = mock_sig
        # when
        enqueue_next_task(chain)
        # then
        mock_sig.apply_async.assert_called()
        self.assertEqual(chain, [])
        mock_logger.debug.assert_called_with(
            "Skipping task as its already queued %s", mock_sig
        )
