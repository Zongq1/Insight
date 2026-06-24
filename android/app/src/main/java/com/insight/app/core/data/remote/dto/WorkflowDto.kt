package com.insight.app.core.data.remote.dto

import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class WorkflowRequest(
    val topic: String,
    val raw_texts: List<String> = emptyList(),
    val keywords: List<String> = emptyList(),
)

@JsonClass(generateAdapter = true)
data class WorkflowResponse(
    val thread_id: String,
    val status: String,
    val final_briefings: List<InsightDto> = emptyList(),
    val errors: List<String> = emptyList(),
    val retry_count: Int = 0,
)
