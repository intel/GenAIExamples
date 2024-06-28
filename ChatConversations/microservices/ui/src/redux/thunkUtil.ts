// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { createAsyncThunk, AsyncThunkPayloadCreator, AsyncThunk } from "@reduxjs/toolkit";

interface ThunkAPIConfig {}

export const createAsyncThunkWrapper = <Returned, ThunkArg = any>(
  type: string,
  thunk: AsyncThunkPayloadCreator<Returned, ThunkArg>, // <-- very unsure of this - have tried many things here
): AsyncThunk<Returned, ThunkArg, ThunkAPIConfig> => {
  return createAsyncThunk<Returned, ThunkArg, ThunkAPIConfig>(
    type,
    // @ts-ignore
    async (arg, thunkAPI) => {
      try {
        // do some stuff here that happens on every action
        return await thunk(arg, thunkAPI);
      } catch (err) {
        // do some stuff here that happens on every error
        return thunkAPI.rejectWithValue(err);
      }
    },
  );
};
