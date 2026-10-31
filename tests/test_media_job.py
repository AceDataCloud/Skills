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

    def test_image_recipe_is_one_watermark_free_2k_image(self):
        api = Mock(return_value={'data': [{'url': 'https://cdn.example/image.jpg'}]})
        with tempfile.TemporaryDirectory() as directory:
            result = job.run('image', 'A book', Path(directory) / 'job.json', api=api, token='test')
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(api.call_count, 1)
        payload = api.call_args.args[1]
        self.assertEqual(payload['size'], '2K')
        self.assertEqual(payload['sequential_image_generation'], 'disabled')
        self.assertIs(payload['watermark'], False)

    def test_authenticated_api_call_does_not_follow_redirects(self):
        from http.server import BaseHTTPRequestHandler, HTTPServer
        from threading import Thread
        from unittest.mock import patch
        requests = []
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                requests.append(self.path)
                self.send_response(302)
                self.send_header('Location', '/unexpected-destination')
                self.end_headers()
            def do_GET(self):
                requests.append(self.path)
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'{}')
            def log_message(self, *args):
                pass
        server = HTTPServer(('127.0.0.1', 0), Handler)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with patch.object(job, 'ORIGIN', f'http://127.0.0.1:{server.server_port}'), patch('urllib.request.getproxies', return_value={}):
                with self.assertRaisesRegex(RuntimeError, 'HTTP 302'):
                    job.call('/wan/videos', {}, 'test-credential')
            self.assertEqual(requests, ['/wan/videos'])
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

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
