// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { User } from "../User/user";

export interface Conversation {
  conversation_id: string;
  user_id: string;
  first_query: string;
  message_count: number | 0;
  created_at?: number;
  updated_at?: number;
  messages?: Message[];
  last_message?: Message;
}

export interface Message {
  message_id: string;
  human: string;
  assistant: string;
  inference_settings: InferenceSettings | null;
  feedback?: null;
  created_at: number;
  updated_at: number;
}

export interface InferenceSettings {
  model: string;
  temperature: string;
  token_limit: number;
  input_token: null;
  output_token: null;
  tags: null;
}

export type ConversationList = Conversation[];

export interface ConversationReducer {
  conversations: ConversationList;
  selectedConversationId: string;
  selectedConversation?: Conversation | null;
  onGoingPrompt: string;
  onGoingResult: string;
}

export type ConversationRequest = {
  conversationId: string;
  user: User;
  prompt: string;
  temperature: number;
  inferenceModel: string;
  tokenLimit: number;
};
