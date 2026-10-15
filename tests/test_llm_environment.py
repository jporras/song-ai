import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


@unittest.skipUnless(shutil.which('powershell.exe'), 'Requires Windows PowerShell')
class LlmEnvironmentTest(unittest.TestCase):
    def test_file_values_are_literal_and_process_overrides_win(self):
        helper = Path(__file__).resolve().parents[1] / 'scripts' / 'llm-environment.ps1'
        with tempfile.TemporaryDirectory(dir=helper.parent.parent) as folder:
            env_file = Path(folder) / '.env'
            env_file.write_text('# comment\nSONG_AI_TEST_BATCH="--batch-size 512 --ubatch-size 256"\n'
                                'SONG_AI_TEST_OVERRIDE=file\nSONG_AI_TEST_LITERAL=$(throw bad)=literal\n'
                                'UNRELATED_TEST_VALUE=ignored\n', encoding='utf-8')
            quote = lambda path: "'" + str(path).replace("'", "''") + "'"
            script = f". {quote(helper)}; $env:SONG_AI_TEST_OVERRIDE='process'; Import-SongAiEnvironment {quote(env_file)}; "
            script += "@{batch=$env:SONG_AI_TEST_BATCH;override=$env:SONG_AI_TEST_OVERRIDE;literal=$env:SONG_AI_TEST_LITERAL;unrelated=$env:UNRELATED_TEST_VALUE} | ConvertTo-Json -Compress"
            result = subprocess.run(['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', script],
                                    capture_output=True, text=True, check=True)
            self.assertFalse(result.stderr.strip(), result.stderr)
            self.assertEqual(json.loads(result.stdout), {
                'batch':'--batch-size 512 --ubatch-size 256', 'override':'process',
                'literal':'$(throw bad)=literal', 'unrelated':None})
