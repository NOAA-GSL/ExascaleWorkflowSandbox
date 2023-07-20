program mpi_hello

  use iso_fortran_env, only : output_unit
  use mpi

  integer :: error
  integer :: world_size, world_rank, name_len, i
  character(len=MPI_MAX_PROCESSOR_NAME) :: host_name
  character(len=6) :: rank
  character(len=6) :: size

  ! Initialize the MPI environment
  call MPI_Init(error)

  ! Get the number of processes
  call MPI_Comm_size(MPI_COMM_WORLD, world_size, error)
  write(size,'(I6)') world_size

  ! Get the rank of the process
  call MPI_Comm_rank(MPI_COMM_WORLD, world_rank, error)
  write(rank,'(I6)') world_rank

  ! Get the name of the processor
  call MPI_Get_processor_name(host_name, name_len, error)

  do i=0, world_size - 1

    call MPI_Barrier(MPI_COMM_WORLD, error)

    if (i==world_rank) then

      ! Print off a hello world message
      write(*,"(A, A, A, A, A, A)")  "Hello world from host ", & 
                                       TRIM(host_name), &
                                       ", rank ", &
                                       TRIM(ADJUSTL(rank)), &
                                       " out of ", &
                                       TRIM(ADJUSTL(size))
    
      ! Flush stdout
      flush(output_unit)

    end if

  end do

  ! Finalize the MPI environment.
  call MPI_Finalize(error)

end program mpi_hello
