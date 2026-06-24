package com.insight.app.core.data.local.dao

import androidx.room.Dao
import androidx.room.Delete
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Update
import com.insight.app.core.data.local.entity.TopicEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface TopicDao {

    @Query("SELECT * FROM topics ORDER BY createdAt DESC")
    fun getAllTopics(): Flow<List<TopicEntity>>

    @Query("SELECT * FROM topics WHERE id = :id")
    suspend fun getTopicById(id: String): TopicEntity?

    @Query("SELECT * FROM topics WHERE name = :name")
    suspend fun getTopicByName(name: String): TopicEntity?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertTopic(topic: TopicEntity)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertTopics(topics: List<TopicEntity>)

    @Update
    suspend fun updateTopic(topic: TopicEntity)

    @Delete
    suspend fun deleteTopic(topic: TopicEntity)

    @Query("SELECT COUNT(*) FROM topics")
    suspend fun count(): Int
}
