package com.insight.app.core.data.remote

import com.insight.app.core.data.remote.dto.CreateTopicRequest
import com.insight.app.core.data.remote.dto.InsightDto
import com.insight.app.core.data.remote.dto.TopicDto
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path

interface ApiService {

    @GET("topics")
    suspend fun getTopics(): Response<List<TopicDto>>

    @POST("topics")
    suspend fun createTopic(@Body request: CreateTopicRequest): Response<TopicDto>

    @GET("topics/{topicId}/insights")
    suspend fun getInsights(@Path("topicId") topicId: String): Response<List<InsightDto>>

    @GET("insights")
    suspend fun getAllInsights(): Response<List<InsightDto>>

    @GET("insights/{insightId}")
    suspend fun getInsight(@Path("insightId") insightId: String): Response<InsightDto>
}
