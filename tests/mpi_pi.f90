program calculatePi

  use mpi

  integer :: error
  integer :: worldSize, worldRank, nameLen
  character(len=MPI_MAX_PROCESSOR_NAME) :: hostname
  character(len=6) :: rank, size
  character(len=10) :: samples
  integer*8 :: i
  integer*8 :: nCircle, nSquare, sumCircle, sumSquare
  real*8    :: randX, randY, distance, pi
  integer   :: timeValues(8)
  real*4    :: start_time, current_time
  
  ! Initialize the MPI environment
  call MPI_Init(error)

  ! Get the number of processes
  call MPI_Comm_size(MPI_COMM_WORLD, worldSize, error)
  write(size,'(I6)') worldSize

  ! Get the rank of the process
  call MPI_Comm_rank(MPI_COMM_WORLD, worldRank, error)
  write(rank,'(I6)') worldRank

  ! Get the name of the processor
  call MPI_Get_processor_name(hostname, nameLen, error)

  if (worldRank == 0) then
    call date_and_time(VALUES=timeValues)
    write(*,"(A,I2.2,A,I2.2,A,I4,A,I2.2,A,I2.2,A,I2.2)") "Start Time = ", timeValues(3), "/", timeValues(2), "/", timeValues(1), &
            " ", timeValues(5), ":", timeValues(6), ":", timeValues(7)
  end if

  ! Initialize the random number seed
  call random_seed()

  nCircle = 0
  nSquare = 0
  pi = 0.0
  call cpu_time(start_time)
  call cpu_time(current_time)
  i = 0
  do while ((current_time - start_time) < 30)
    i = i + 1
    call random_number(randX)
    call random_number(randY)

    distance = randX * randX + randY * randY

    if (distance <= 1) then
      nCircle = nCircle + 1
    end if
    nSquare = nSquare + 1

    call cpu_time(current_time)

  end do

  pi = 4.0 * nCircle / nSquare

  write(samples,'(I10)') i
  write(*,"(A,A,A,A,A,A,A,F15.13,A,A)") "Host ", TRIM(hostname), " rank ", &
          TRIM(ADJUSTL(rank)), " of ", TRIM(ADJUSTL(size)), &
          " local approximation of pi = ", pi, " after ", &
          TRIM(ADJUSTL(samples)), "samples"

  call MPI_Reduce(nCircle, sumCircle, 1, MPI_LONG, MPI_SUM, 0, MPI_COMM_WORLD, error)
  call MPI_Reduce(nSquare, sumSquare, 1, MPI_LONG, MPI_SUM, 0, MPI_COMM_WORLD, error)

  if (worldRank == 0) then
    write(*,"(A,F15.13)") "Collective approximation of pi = ", 4.0 * sumCircle / sumSquare
  end if

  if (worldRank == 0) then
    call date_and_time(VALUES=timeValues)
    write(*,"(A,I2.2,A,I2.2,A,I4,A,I2.2,A,I2.2,A,I2.2)") "End Time = ", timeValues(3), "/", timeValues(2), "/", timeValues(1), & 
            " ", timeValues(5), ":", timeValues(6), ":", timeValues(7)
  end if

  ! Finalize the MPI environment.
  call MPI_Finalize(error)

end program calculatePi
