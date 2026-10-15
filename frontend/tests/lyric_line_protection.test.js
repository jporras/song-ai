import test from 'node:test';
import assert from 'node:assert/strict';
import { protectedLinesUnchanged } from '../src/lyric_line_protection.js';
test('literal and position stay protected while other lines can change', () => {
  const section = {text:'Alma\nVerso',protected_lines:[0]};
  assert.equal(protectedLinesUnchanged(section,'Alma\nNuevo verso'),true);
  assert.equal(protectedLinesUnchanged(section,'Isabella\nVerso'),false);
  assert.equal(protectedLinesUnchanged(section,'Intro\nAlma\nVerso'),false);
});
