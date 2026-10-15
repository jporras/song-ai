import { protectedLinesUnchanged } from './lyric_line_protection.js';

export function canApplySectionProposal(proposal, section, projectId, context) {
  return Boolean(proposal && section && !section.locked && proposal.projectId === projectId
    && proposal.context === context && proposal.sectionSnapshot === JSON.stringify(section)
    && protectedLinesUnchanged(section, proposal.text));
}
