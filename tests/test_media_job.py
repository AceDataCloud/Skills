import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

spec = importlib.util.spec_from_file_location('media_job', Path(__file__).parents[1] / 'skills/_shared/scripts/media_job.py')
job = importlib.util.module_from_spec(spec)
spec.loader.exec_module(job)


class MediaJobs(unittest.TestCase):
    def test_completed_task_envelope_and_replay_submit_once(self):
        api = Mock(side_effect=[{'task_id': 'original'}, {'finished_at': 1, 'response': {'success': True, 'data': {'video_url': 'https://cdn.example/video.mp4'}}}])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'job.json'
            first = job.run('video', 'A quiet lake', path, api=api, token='test')
            second = job.run('video', 'A quiet lake', path, api=api, token='test')
            self.assertEqual(first, second)
            self.assertEqual(first['status'], 'completed')
            self.assertEqual(api.call_count, 2)
            self.assertEqual(api.call_args_list[0].args[1]['duration'], 5)
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_provider_failure_finishes_without_polling_forever(self):
        api = Mock(side_effect=[{'task_id': 'failed'}, {'finished_at': 1, 'response': {'success': False, 'error': {'code': 'api_error'}}}])
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(job.run('video', 'A lake', Path(directory) / 'job.json', api=api, token='test')['status'], 'failed')
        self.assertEqual(api.call_count, 2)

    def test_lost_submission_response_is_never_retried(self):
        api = Mock(side_effect=TimeoutError('network timeout'))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'job.json'
            with self.assertRaises(TimeoutError):
                job.run('image', 'A book', path, api=api, token='test')
            with self.assertRaisesRegex(RuntimeError, 'unknown'):
                job.run('image', 'A book', path, api=api, token='test')
        self.assertEqual(api.call_count, 1)

    def test_state_cannot_be_reused_for_another_request(self):
        api = Mock(return_value={'audio_url': 'https://cdn.example/voice.mp3'})
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'job.json'
            self.assertEqual(job.run('audio', 'Hello', path, api=api, token='test')['status'], 'completed')
            with self.assertRaises(ValueError):
                job.run('audio', 'Different', path, api=api, token='test')
        self.assertEqual(api.call_count, 1)


if __name__ == '__main__':
    unittest.main()
