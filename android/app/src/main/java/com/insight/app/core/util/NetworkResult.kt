package com.insight.app.core.util

import retrofit2.HttpException
import retrofit2.Response
import java.io.IOException

sealed class NetworkResult<out T> {
    data class Success<T>(val data: T) : NetworkResult<T>()
    data class Error(val code: Int? = null, val message: String? = null) : NetworkResult<Nothing>()
    data object Loading : NetworkResult<Nothing>()
}

suspend fun <T> safeApiCall(call: suspend () -> Response<T>): NetworkResult<T> {
    return try {
        val response = call()
        if (response.isSuccessful) {
            response.body()?.let {
                NetworkResult.Success(it)
            } ?: NetworkResult.Error(code = response.code(), message = "Empty body")
        } else {
            NetworkResult.Error(
                code = response.code(),
                message = response.errorBody()?.string() ?: "Unknown error"
            )
        }
    } catch (e: HttpException) {
        NetworkResult.Error(code = e.code(), message = e.message())
    } catch (e: IOException) {
        NetworkResult.Error(message = "Network connection failed")
    } catch (e: Exception) {
        NetworkResult.Error(message = e.localizedMessage ?: "Unknown error")
    }
}

fun <T, R> NetworkResult<T>.map(transform: (T) -> R): NetworkResult<R> {
    return when (this) {
        is NetworkResult.Success -> NetworkResult.Success(transform(data))
        is NetworkResult.Error -> this
        is NetworkResult.Loading -> this
    }
}
