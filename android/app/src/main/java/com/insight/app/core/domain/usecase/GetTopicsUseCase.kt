package com.insight.app.core.domain.usecase

import com.insight.app.core.data.repository.TopicRepository
import com.insight.app.core.domain.model.Topic
import com.insight.app.core.util.NetworkResult
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject

class GetTopicsUseCase @Inject constructor(
    private val repository: TopicRepository,
) {
    operator fun invoke(): Flow<List<Topic>> {
        return repository.getTopics()
    }

    suspend fun createTopic(name: String, keywords: List<String>): NetworkResult<Topic> {
        return repository.createTopic(name, keywords)
    }
}
