package com.insight.app.core.data.remote.dto

import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class TopicDto(
    val id: String,
    val name: String,
    val keywords: List<String>,
    val last_fetched_at: String?,
)

@JsonClass(generateAdapter = true)
data class CreateTopicRequest(
    val name: String,
    val keywords: List<String>,
)
