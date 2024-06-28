// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { configureStore } from "@reduxjs/toolkit";
import userReducer from "./User/userSlice";
import conversationReducer from "./Conversation/conversationSlice";
import { TypedUseSelectorHook, useDispatch, useSelector } from "react-redux";

export const store = configureStore({
  reducer: {
    userReducer,
    conversationReducer,
  },
  devTools: import.meta.env.PROD,
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: false,
    }),
});
export type AppDispatch = typeof store.dispatch;
export type RootState = ReturnType<typeof store.getState>;

export const useAppDispatch: () => AppDispatch = useDispatch;
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;
