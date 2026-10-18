import test from "node:test";
import assert from "node:assert/strict";
import { productionNextAction } from "../src/production_guidance.js";

const revision = {revision_id:"r1",user_confirmation_status:"confirmed"};
const plan = {effective_status:"approved",inputs_current:true,plan:{spec_revision_id:"r1"}};

test("Production indica la acción siguiente sin confirmar ni generar por el usuario", () => {
  assert.equal(productionNextAction({projectId:"",revision,plan}).target,"library");
  assert.equal(productionNextAction({projectId:"song",revision:{...revision,user_confirmation_status:"pending"},plan}).target,"spec");
  assert.equal(productionNextAction({projectId:"song",revision,plan:null}).target,"plan");
  const editingPlan = productionNextAction({projectId:"song",revision,plan:null,planDraftOpen:true});
  assert.equal(editingPlan.target,"plan-editor");
  assert.match(editingPlan.message,/Crear plan para revisar/);
  assert.equal(productionNextAction({projectId:"song",revision,plan:{...plan,effective_status:"candidate"}}).target,"plan-approval");
  assert.equal(productionNextAction({projectId:"song",revision,plan}).target,"final");
  assert.equal(productionNextAction({projectId:"song",revision,plan,resourceBlocked:true}).target,"resources");
  const automaticRelease = productionNextAction({projectId:"song",revision,plan,resourceBlocked:true,automaticModelReleaseAvailable:true});
  assert.equal(automaticRelease.target,"final");
  assert.match(automaticRelease.message,/cerrará Gemma\/Qwen/);
  assert.match(productionNextAction({projectId:"song",revision,plan}).message,/sample previo es opcional/);
  assert.equal(productionNextAction({projectId:"song",revision,plan,exportReady:true}).target,"downloads");
});
