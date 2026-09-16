import type { AgentCapabilityManifest, AgentEndpointKey, AgentFeatureKey } from "../types/api";

// 第 02 课精简版：只保留能力判断，数据转换逻辑（normalizeAgentObservation 等）在后续课程按需加回。

export function isAgentFeatureEnabled(capabilities: AgentCapabilityManifest, feature: AgentFeatureKey) {
  return capabilities.features?.[feature] === true;
}

export function isAgentEndpointEnabled(capabilities: AgentCapabilityManifest, endpoint: AgentEndpointKey) {
  return capabilities.endpoints?.[endpoint] === true;
}
