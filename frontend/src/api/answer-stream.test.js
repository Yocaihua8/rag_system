import { afterEach, describe, expect, it, vi } from "vitest";

import { askQuestionStream } from "./answer.js";

class FakeEventSource {
  static instances = [];

  constructor(url) {
    this.url = url;
    this.listeners = {};
    this.closed = false;
    FakeEventSource.instances.push(this);
  }

  addEventListener(event, handler) {
    this.listeners[event] = handler;
  }

  emit(event, data) {
    this.listeners[event]?.({ data: JSON.stringify(data) });
  }

  close() {
    this.closed = true;
  }
}

describe("askQuestionStream", () => {
  afterEach(() => {
    FakeEventSource.instances = [];
    vi.unstubAllGlobals();
  });

  it("opens an encoded EventSource URL and accumulates token text", async () => {
    vi.stubGlobal("EventSource", FakeEventSource);
    const onToken = vi.fn();

    const stream = askQuestionStream({
      projectId: "p 1",
      question: "  默认入口是什么？ ",
      sessionId: "s1",
      toolRunId: "run1",
      parentMessageId: "m1",
      handlers: { onToken },
    });
    const source = FakeEventSource.instances[0];

    expect(source.url).toBe(
      "/api/answer/stream?project_id=p+1&question=%E9%BB%98%E8%AE%A4%E5%85%A5%E5%8F%A3%E6%98%AF%E4%BB%80%E4%B9%88%EF%BC%9F&session_id=s1&tool_run_id=run1&parent_message_id=m1",
    );

    source.emit("token", { text: "知" });
    source.emit("token", { text: "识岛" });
    source.emit("done", { answer: "知识岛", message: { id: "m2" } });

    await expect(stream.promise).resolves.toEqual({ answer: "知识岛", message: { id: "m2" } });
    expect(onToken).toHaveBeenNthCalledWith(1, "知", "知");
    expect(onToken).toHaveBeenNthCalledWith(2, "知识岛", "识岛");
    expect(source.closed).toBe(true);
  });

  it("rejects stream errors and aborts active streams with AbortError", async () => {
    vi.stubGlobal("EventSource", FakeEventSource);

    const failed = askQuestionStream({ projectId: "p1", question: "Q" });
    FakeEventSource.instances[0].emit("answer_error", { error: "模型失败" });
    await expect(failed.promise).rejects.toThrow("模型失败");
    expect(FakeEventSource.instances[0].closed).toBe(true);

    const active = askQuestionStream({ projectId: "p1", question: "Q" });
    active.abort();
    await expect(active.promise).rejects.toMatchObject({ name: "AbortError", message: "已取消本次提问" });
    expect(FakeEventSource.instances[1].closed).toBe(true);
  });
});
