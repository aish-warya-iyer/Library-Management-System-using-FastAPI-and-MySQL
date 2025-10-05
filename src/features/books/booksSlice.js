import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import api from "../../lib/api";

// -------- thunks --------
export const fetchBooks = createAsyncThunk(
  "books/fetchBooks",
  async (params = {}, { rejectWithValue }) => {
    try {
      const res = await api.get("/books", { params });
      return res.data;
    } catch (err) {
      return rejectWithValue(err.response?.data || { detail: "Fetch failed" });
    }
  }
);

export const createBook = createAsyncThunk(
  "books/createBook",
  async (payload, { rejectWithValue }) => {
    try {
      const res = await api.post("/books", payload);
      return res.data;
    } catch (err) {
      return rejectWithValue(err.response?.data || { detail: "Create failed" });
    }
  }
);

export const updateBook = createAsyncThunk(
  "books/updateBook",
  async ({ id, changes }, { rejectWithValue }) => {
    try {
      const res = await api.put(`/books/${id}`, changes);
      return res.data;
    } catch (err) {
      return rejectWithValue(err.response?.data || { detail: "Update failed" });
    }
  }
);

export const deleteBook = createAsyncThunk(
  "books/deleteBook",
  async (id, { rejectWithValue }) => {
    try {
      await api.delete(`/books/${id}`);
      return id;
    } catch (err) {
      return rejectWithValue(err.response?.data || { detail: "Delete failed" });
    }
  }
);

// -------- slice --------
const booksSlice = createSlice({
  name: "books",
  initialState: {
    items: [],
    status: "idle", // idle | loading | succeeded | failed
    error: null,
  },
  reducers: {},
  extraReducers: (builder) => {
    builder
      // fetch
      .addCase(fetchBooks.pending, (s) => {
        s.status = "loading";
        s.error = null;
      })
      .addCase(fetchBooks.fulfilled, (s, a) => {
        s.status = "succeeded";
        s.items = a.payload;
      })
      .addCase(fetchBooks.rejected, (s, a) => {
        s.status = "failed";
        s.error = a.payload?.detail || "Failed to fetch books";
      })
      // create
      .addCase(createBook.pending, (s) => {
        s.error = null;
      })
      .addCase(createBook.fulfilled, (s, a) => {
        s.items.unshift(a.payload);
      })
      .addCase(createBook.rejected, (s, a) => {
        s.error = a.payload?.detail || "Failed to create book";
      })
      // update
      .addCase(updateBook.fulfilled, (s, a) => {
        const idx = s.items.findIndex((b) => b.id === a.payload.id);
        if (idx !== -1) s.items[idx] = a.payload;
      })
      .addCase(updateBook.rejected, (s, a) => {
        s.error = a.payload?.detail || "Failed to update book";
      })
      // delete
      .addCase(deleteBook.fulfilled, (s, a) => {
        s.items = s.items.filter((b) => b.id !== a.payload);
      })
      .addCase(deleteBook.rejected, (s, a) => {
        s.error = a.payload?.detail || "Failed to delete book";
      });
  },
});

export default booksSlice.reducer;
