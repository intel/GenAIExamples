// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { PayloadAction, createSlice } from "@reduxjs/toolkit";
import { Conversation, ConversationList, ConversationReducer, ConversationRequest, Message } from "./conversation";
import client from "../../common/client";
import { User } from "../User/user";
import { createAsyncThunkWrapper } from "../thunkUtil";
import { RootState, store } from "../store";
import { fetchEventSource } from "@microsoft/fetch-event-source";

const initialState: ConversationReducer = {
  conversations: [],
  selectedConversationId: "",
  selectedConversation: {
    message_count: 0,
    messages: [],
    first_query: "",
    conversation_id: "",
    user_id: "",
  },
  onGoingPrompt: "",
  onGoingResult: "",
};

const SERVICE_URL = import.meta.env.VITE_SERVICE_URL;

export const getAllConversations = createAsyncThunkWrapper("conversation/fetchAllConversation", async (user: User) => {
  const response = await client.get<{ data: ConversationList }>(`${SERVICE_URL}/conversations?user=${user.name}`);
  return response.data.data;
});

export const getConversationById = createAsyncThunkWrapper(
  "users/fetchConversationById",
  async ({ user, conversationId }: { user: User; conversationId: string }, {}) => {
    const response = await client.get<Conversation>(`${SERVICE_URL}/conversations/${conversationId}?user=${user.name}`);
    return response.data;
  },
);

export const deleteConversationById = createAsyncThunkWrapper(
  "users/deleteConversationById",
  async ({ user, conversationId }: { user: User; conversationId: string }, {}) => {
    await client.delete(`${SERVICE_URL}/conversations/${conversationId}?user=${user.name}`);
    return conversationId;
  },
);

export const conversationSlice = createSlice({
  name: "conversation",
  initialState,
  reducers: {
    setSelectedConversationId: (state, action: PayloadAction<string>) => {
      state.selectedConversationId = action.payload;
    },
    setOnGoingResult: (state, action: PayloadAction<string>) => {
      state.onGoingResult = action.payload;
    },
    setOnGoingPrompt: (state, action: PayloadAction<string>) => {
      state.onGoingPrompt = action.payload;
    },
    setSelectedConversation: (state, action: PayloadAction<Conversation>) => {
      state.selectedConversation = action.payload;
      state.selectedConversationId = action.payload.conversation_id;
    },
    addMessageToSelectedConversation: (state, action: PayloadAction<Message>) => {
      state.selectedConversation?.messages?.push(action.payload);
    },
    addConversationToConversations: (state, action: PayloadAction<Conversation>) => {
      state.conversations.unshift(action.payload);
    },
    newConversation: (state) => {
      state.selectedConversationId = "";
      state.selectedConversation = {
        message_count: 0,
        messages: [],
        first_query: "",
        conversation_id: "",
        user_id: "",
      };
    },

    // doConversation: (state, action: PayloadAction<ConversationRequest>) => {
    //   console.log("inside action");

    // },
  },
  extraReducers(builder) {
    builder.addCase(getAllConversations.fulfilled, (state, action) => {
      console.log("fullll");
      state.conversations = action.payload;
    }),
      builder.addCase(getAllConversations.rejected, (state) => {
        state.conversations = [];
      }),
      builder.addCase(getConversationById.fulfilled, (state, action) => {
        state.selectedConversation = action.payload;
      }),
      builder.addCase(deleteConversationById.fulfilled, (state, action) => {
        console.log("deleted successfully");
        state.conversations = state.conversations.filter((x) => x.conversation_id !== action.payload);
        state.selectedConversationId = "";
        state.selectedConversation = {
          message_count: 0,
          messages: [],
          first_query: "",
          conversation_id: "",
          user_id: "",
        };
      });
    builder.addCase(deleteConversationById.rejected, (_state, action) => {
      console.log("deleted failed", action);
    });
  },
});

export const {
  setSelectedConversationId,
  setOnGoingPrompt,
  setOnGoingResult,
  addMessageToSelectedConversation,
  setSelectedConversation,
  addConversationToConversations,
  newConversation,
} = conversationSlice.actions;
export const conversationSelector = (state: RootState) => state.conversationReducer;
export default conversationSlice.reducer;

export const doConversation = (conversationRequest: ConversationRequest) => {
  const { user, prompt, conversationId, temperature, inferenceModel, tokenLimit } = conversationRequest;
  store.dispatch(setOnGoingPrompt(prompt));
  let body = {
    messages: [{ role: "user", content: prompt }],
    temperature,
    model: inferenceModel,
    max_tokens: tokenLimit,
    stream: true,
  };

  let conversation: Conversation;
  let result = "";
  let conversationURL = `${SERVICE_URL}/conversations`;
  if (conversationId) {
    conversationURL += `/${conversationId}`;
  }
  conversationURL += `?user=${user.name}`;
  try {
    fetchEventSource(conversationURL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
      openWhenHidden: true,
      async onopen(response) {
        if (response.ok) {
          return;
        } else if (response.status >= 400 && response.status < 500 && response.status !== 429) {
          let e = await response.json();
          console.log(e);
          throw Error(e.error.message);
        } else {
          console.log("error", response);
        }
      },
      onmessage(msg) {
        if (msg.data) {
          try {
            conversation = JSON.parse(msg.data);
            result += conversation.last_message?.assistant;
            store.dispatch(setOnGoingResult(result));
            // state.onGoingResult += prev_message.assistant;
            // console.log(state.onGoingPrompt)
          } catch (e) {
            console.log("something wrong in msg", e);
            throw e;
          }
        }
      },
      onerror(err) {
        console.log("error", err);
        store.dispatch(setOnGoingPrompt(""));
        store.dispatch(setOnGoingResult(""));
        //notify here
        throw err;
        //handle error
      },
      onclose() {
        //handle close
        store.dispatch(setOnGoingPrompt(""));
        store.dispatch(setOnGoingResult(""));
        if (!conversationId) {
          store.dispatch(
            addConversationToConversations({
              ...conversation,
            }),
          );
          store.dispatch(
            setSelectedConversation({
              ...conversation,
              messages: [],
            }),
          );
        }
        if (conversation.last_message) {
          store.dispatch(addMessageToSelectedConversation(conversation.last_message));
        }
      },
    });
  } catch (err) {
    console.log(err);
  }
};
