import test from "node:test";
import assert from "node:assert/strict";
import { productionNextAction } from "../src/production_guidance.js";

const revision = {revision_id:"r1",user_confirmation_status:"confirmed"};
const plan = {effective_status:"approved",inputs_current:true,plan:{spec_revision_id:"r1"}};

test("Production indica la acción siguiente sin confirmar ni generar por el usuario", () => {
  assert.equal(productionNextAction({projectId:"",revision,plan}).target,"library");
  assert.equal(productionNextAction({projectId:"song",revision:{...revision,user_confirmation_status:"pending"},plan}).target,"spec");
  assert.equal(productionNextAction({projectId:"song",revision,plan:null}).target,"plan");
  assert.equal(productionNextAction({projectId:"song",revision,plan}).target,"final");
  assert.equal(productionNextAction({projectId:"song",revision,plan,resourceBlocked:true}).target,"resources");
  assert.match(productionNextAction({projectId:"song",revision,plan}).message,/sample previo es opcional/);
  assert.equal(productionNextAction({projectId:"song",revision,plan,exportReady:true}).target,"downloads");
});
