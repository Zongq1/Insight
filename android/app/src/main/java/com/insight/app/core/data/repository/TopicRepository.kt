package com.insight.app.core.data.repository

import com.insight.app.core.data.local.dao.TopicDao
import com.insight.app.core.data.local.entity.TopicEntity
import com.insight.app.core.data.remote.ApiService
import com.insight.app.core.data.remote.dto.CreateTopicRequest
import com.insight.app.core.data.remote.dto.TopicDto
import com.insight.app.core.domain.model.Topic
import com.insight.app.core.util.NetworkResult
import com.insight.app.core.util.safeApiCall
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class TopicRepository @Inject constructor(
    private val topicDao: TopicDao,
    private val apiService: ApiService,
) {
    fun getTopics(): Flow<List<Topic>> {
        return topicDao.getAllTopics().map { entities ->
            entities.map { it.toDomain() }
        }
    }

    suspend fun createTopic(name: String, keywords: List<String>): NetworkResult<Topic> {
        return when (val result = safeApiCall {
            apiService.createTopic(CreateTopicRequest(name, keywords))
        }) {
            is NetworkResult.Success -> {
                val topic = result.data.toDomain()
                topicDao.insertTopic(topic.toEntity())
                NetworkResult.Success(topic)
            }
            is NetworkResult.Error -> result
            is NetworkResult.Loading -> result
        }
    }

    private fun TopicEntity.toDomain() = Topic(
        id = id,
        name = name,
        keywords = emptyList(),
        lastFetchedAt = lastFetchedAt?.toString(),
    )

    private fun Topic.toEntity() = TopicEntity(
        id = id,
        name = name,
        keywordsJson = "[]",
    )

    private fun TopicDto.toDomain() = Topic(
        id = id,
        name = name,
        keywords = keywords,
        lastFetchedAt = last_fetched_at,
    )
}
